import os
import time
import requests
import psycopg2
import pandas as pd
import numpy as np
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config
DATABASE_URL = os.environ.get("DATABASE_URL")
PROMETHEUS_URL = os.environ.get("PROMETHEUS_URL", "http://prometheus:9090")
PUSHGATEWAY_URL = os.environ.get("PUSHGATEWAY_URL", "http://pushgateway:9091")
MODEL_ALIAS = os.environ.get("MODEL_ALIAS", "Staging")
MODEL_NAME = os.environ.get("MODEL_NAME", "credit-risk-model")

def wait_for_services():
    """Wake-up loop for Render free-tier sleeping services."""
    endpoints = [
        f"{PROMETHEUS_URL}/-/healthy",
        f"{PUSHGATEWAY_URL}/-/healthy"
    ]
    
    max_retries = 60 # (5s * 100)
    for i in range(max_retries):
        awake = []
        for url in endpoints:
            try:
                resp = requests.get(url, timeout=5)
                awake.append(resp.status_code in [200, 202])
            except Exception:
                awake.append(False)
        
        if all(awake):
            logger.info("Prometheus and Pushgateway are awake!")
            return True
            
        logger.info(f"Waiting for services to wake up... (Attempt {i+1}/{max_retries})")
        time.sleep(5)
        
    logger.error("Timeout waiting for services to wake up.")
    return False

def calculate_psi(expected, actual, buckets=10):
    """Calculates Population Stability Index (PSI)."""
    def scale_range(s, min_val, max_val):
        return (s - min_val) / (max_val - min_val)
        
    breakpoints = np.arange(0, buckets + 1) / buckets
    
    expected_perc = np.histogram(expected, breakpoints)[0] / len(expected)
    actual_perc = np.histogram(actual, breakpoints)[0] / len(actual)
    
    # Avoid div by zero
    expected_perc = np.where(expected_perc == 0, 0.0001, expected_perc)
    actual_perc = np.where(actual_perc == 0, 0.0001, actual_perc)
    
    psi_value = np.sum((actual_perc - expected_perc) * np.log(actual_perc / expected_perc))
    return psi_value

def run_drift_job():
    if not wait_for_services():
        return
        
    logger.info("Connecting to Supabase...")
    conn = psycopg2.connect(DATABASE_URL)
    
    # Get last 24h of predictions
    query = """
        SELECT probability 
        FROM prediction_logs 
        WHERE ts >= NOW() - INTERVAL '24 hours'
    """
    df_actual = pd.read_sql(query, conn)
    conn.close()
    
    if len(df_actual) == 0:
        logger.info("No predictions in the last 24h. Exiting.")
        return
        
    import mlflow
    from mlflow.tracking import MlflowClient
    
    dagshub_user = os.environ.get("DAGSHUB_USER")
    dagshub_repo = os.environ.get("DAGSHUB_REPO")
    dagshub_token = os.environ.get("DAGSHUB_TOKEN")
    
    if dagshub_user and dagshub_repo and dagshub_token:
        os.environ["MLFLOW_TRACKING_USERNAME"] = dagshub_user
        os.environ["MLFLOW_TRACKING_PASSWORD"] = dagshub_token
        mlflow.set_tracking_uri(f"https://dagshub.com/{dagshub_user}/{dagshub_repo}.mlflow")
        
    client = MlflowClient()
    try:
        logger.info(f"Fetching model version for '{MODEL_NAME}' with alias '{MODEL_ALIAS}'...")
        model_version = client.get_model_version_by_alias(MODEL_NAME, MODEL_ALIAS)
        artifact_path = client.download_artifacts(model_version.run_id, "baseline_probs.npy")
        expected_probs = np.load(artifact_path)
        logger.info(f"Loaded expected_probs from MLflow run {model_version.run_id} (alias: {MODEL_ALIAS}). Size: {len(expected_probs)}")
    except Exception as e:
        logger.error(f"Failed to load baseline_probs from MLflow: {e}")
        return
    
    actual_probs = df_actual['probability'].values
    
    psi_score = calculate_psi(expected_probs, actual_probs)
    logger.info(f"Calculated PSI Score: {psi_score}")
    
    # Push to Prometheus Pushgateway
    registry = CollectorRegistry()
    g = Gauge('model_psi_score', 'Population Stability Index of model predictions', registry=registry)
    g.set(psi_score)
    
    try:
        push_to_gateway(PUSHGATEWAY_URL, job='drift_monitor', registry=registry)
        logger.info("Successfully pushed metrics to Pushgateway.")
    except Exception as e:
        logger.error(f"Failed to push metrics: {e}")

if __name__ == "__main__":
    run_drift_job()
