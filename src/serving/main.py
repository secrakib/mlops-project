import os
import pickle
import pandas as pd
import shap
import mlflow
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from prometheus_fastapi_instrumentator import Instrumentator

from src.serving.config import settings, load_serving_config, load_training_config
from src.serving.schemas import ScoreRequest, ScoreResponse
from src.serving.middleware import RequestIdMiddleware
from src.common.logging_config import setup_prediction_logger
from src.db.models import init_db

# Globals to hold loaded models/assets
mlflow_model = None
shap_explainer = None
cost_matrix = None
serving_cfg = None
training_cfg = None

logger = setup_prediction_logger(db_url=settings.DATABASE_URL)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global mlflow_model, shap_explainer, cost_matrix, serving_cfg, training_cfg
    
    logger.info("Initializing Supabase Database schema...")
    init_db(settings.DATABASE_URL)
    
    logger.info("Loading configurations...")
    serving_cfg = load_serving_config()
    training_cfg = load_training_config()
    cost_matrix = training_cfg["evaluation"]["cost_matrix"]
    
    # Configure MLflow auth (needed to pull model & SHAP artifacts)
    os.environ["MLFLOW_TRACKING_USERNAME"] = settings.DAGSHUB_USER
    os.environ["MLFLOW_TRACKING_PASSWORD"] = settings.DAGSHUB_TOKEN
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    
    # Load MLflow Model
    model_uri = f"models:/{serving_cfg['model_name']}@{settings.MODEL_ALIAS}"
    logger.info(f"Loading MLflow model: {model_uri}")
    mlflow_model = mlflow.sklearn.load_model(model_uri)
    
    # Download SHAP background
    logger.info("Resolving MLflow run to fetch SHAP background...")
    client = mlflow.tracking.MlflowClient()
    try:
        model_version = client.get_model_version_by_alias(serving_cfg['model_name'], settings.MODEL_ALIAS)
        run_id = model_version.run_id
        
        import joblib
        shap_bg_path = client.download_artifacts(run_id, "shap_background.pkl")
        shap_background = joblib.load(shap_bg_path)
            
        # We need to wrap the prediction function to reconstruct the DataFrame,
        # because KernelExplainer converts the DataFrame into a numpy array,
        # and the sklearn pipeline expects a DataFrame with column names.
        logger.info("Initializing SHAP KernelExplainer...")
        
        # Define prediction wrapper
        def predict_fn(X):
            import pandas as pd
            cols = training_cfg['features']['selected_numeric_features']
            df_x = pd.DataFrame(X, columns=cols)
            return mlflow_model.predict_proba(df_x)
            
        shap_explainer = shap.KernelExplainer(predict_fn, shap_background)
    except Exception as e:
        logger.error(f"Failed to load SHAP artifact: {e}")
        shap_explainer = None # We will just return empty dict if this fails
        
    logger.info("FastAPI lifecycle startup complete.")
    yield
    
    logger.info("FastAPI shutting down...")

app = FastAPI(title="Credit Risk Scoring API", lifespan=lifespan)

# Add Middleware
app.add_middleware(RequestIdMiddleware)

origins = [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics exposure
Instrumentator().instrument(app).expose(app)

@app.get("/health")
def health_check():
    """Liveness probe. Essential for Render cold starts and monitoring."""
    if not mlflow_model:
        raise HTTPException(status_code=503, detail="Model not loaded yet.")
    return {"status": "ok", "model_loaded": True}

@app.post("/score", response_model=ScoreResponse)
def score(request: ScoreRequest):
    """Predicts default probability and returns SHAP values."""
    from src.common.logging_config import request_id_var
    req_id = request_id_var.get()
    
    # 1. Convert to DataFrame (respects order of Pydantic model)
    data_dict = request.model_dump()
    df = pd.DataFrame([data_dict])
    
    # 2. Predict Probability (Class 1 = Default)
    # predict_proba returns [[prob_0, prob_1]]
    proba = float(mlflow_model.predict_proba(df)[0][1])
    
    # 3. Decision Logic (Cost-Matrix Threshold)
    threshold = cost_matrix["fp_cost"] / (cost_matrix["fp_cost"] + cost_matrix["fn_cost"])
    decision = "Reject" if proba >= threshold else "Approve"
    
    # 4. SHAP Explanations (avoiding Matplotlib plots entirely)
    feat_shap_dict = {}
    if shap_explainer:
        # For KernelExplainer, shap_values returns a list of arrays (one for each class)
        # We take index 1 (default class). 
        # shap_values[1] shape: (1, n_features)
        import numpy as np
        shap_vals = shap_explainer.shap_values(df, silent=True)
        # Handle depending on shap version / model output
        class_1_shap = shap_vals[1][0] if isinstance(shap_vals, list) else shap_vals[0]
        class_1_shap = np.array(class_1_shap).flatten()
        
        # Zip with original features from config, as df might have different order
        cols = training_cfg['features']['selected_numeric_features']
        feat_shap_dict = dict(zip(cols, [float(x) for x in class_1_shap]))
        
    # 5. Central Logging (stdout + Supabase Postgres)
    log_payload = {
        "request_json": data_dict,
        "probability": proba,
        "decision": decision,
        "model_version": settings.MODEL_ALIAS,
        "latency_ms": 0.0,
    }
    # This automatically includes the request_id thanks to our RequestIdFilter
    logger.info(log_payload)
    
    return ScoreResponse(
        probability=proba,
        decision=decision,
        shap_values=feat_shap_dict,
        request_id=req_id
    )
