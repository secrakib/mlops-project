import os
import yaml
import mlflow
import pandas as pd
from prefect import task, flow
from dotenv import load_dotenv

import src.features.feature_pipeline as fp
from src.training.train import train_logistic_regression, train_xgboost
from src.training.evaluate import calibrate_model, compute_metrics, optimize_threshold, compute_expected_cost, plot_calibration_curve_to_file

def setup_mlflow():
    load_dotenv()
    dagshub_user = os.getenv("DAGSHUB_USER")
    dagshub_repo = os.getenv("DAGSHUB_REPO")
    dagshub_token = os.getenv("DAGSHUB_TOKEN")
    
    if dagshub_user and dagshub_repo and dagshub_token:
        os.environ["MLFLOW_TRACKING_USERNAME"] = dagshub_user
        os.environ["MLFLOW_TRACKING_PASSWORD"] = dagshub_token
        tracking_uri = f"https://dagshub.com/{dagshub_user}/{dagshub_repo}.mlflow"
        mlflow.set_tracking_uri(tracking_uri)
    
    mlflow.set_experiment("credit-risk-scoring")

@task
def load_data_task(config):
    return fp.load_data(config['data']['path'])

@task
def validate_data_task(df, config):
    schema = fp.get_pandera_schema(config, is_inference=False)
    return schema.validate(df)

@task
def split_data_task(df, config):
    df_train_raw, df_val_raw, df_test_raw = fp.temporal_split(
        df, 
        val_ratio=config['data']['split_ratios']['val'],
        test_ratio=config['data']['split_ratios']['test']
    )
    return df_train_raw, df_val_raw, df_test_raw

@task
def build_features_task(df_train_raw, df_val_raw, df_test_raw, config):
    df_train = fp.build_features(df_train_raw, config)
    df_val = fp.build_features(df_val_raw, config)
    df_test = fp.build_features(df_test_raw, config)
    return df_train, df_val, df_test

@task
def train_and_evaluate(df_train, df_val, df_test, config):
    X_train = df_train.drop(columns=['target'])
    y_train = df_train['target']
    
    X_val = df_val.drop(columns=['target'])
    y_val = df_val['target']
    
    X_test = df_test.drop(columns=['target'])
    y_test = df_test['target']
    
    cost_matrix = config['evaluation']['cost_matrix']
    
    # Create preprocessor
    numeric_features = config['features']['selected_numeric_features']
    preprocessor = fp.create_preprocessor(numeric_features)
    
    with mlflow.start_run() as run:
        # Train baseline
        lr_model = train_logistic_regression(X_train, y_train, preprocessor)
        lr_preds = lr_model.predict_proba(X_val)[:, 1]
        lr_metrics = compute_metrics(y_val, lr_preds)
        print(f"LR Val Metrics: {lr_metrics}")
        
        # Train challenger
        xgb_model = train_xgboost(X_train, y_train, config['model']['xgboost_grid'], preprocessor)
        xgb_preds = xgb_model.predict_proba(X_val)[:, 1]
        xgb_metrics = compute_metrics(y_val, xgb_preds)
        print(f"XGB Val Metrics: {xgb_metrics}")
        
        # Selection logic (e.g., higher AUC-PR)
        if xgb_metrics['auc_pr'] >= lr_metrics['auc_pr']:
            best_model = xgb_model
            best_name = "xgboost"
        else:
            best_model = lr_model
            best_name = "logistic_regression"
            
        print(f"Winning model: {best_name}")
        mlflow.log_param("model_type", best_name)
        
        # Calibration on Val
        calibrated_model = calibrate_model(best_model, X_val, y_val)
        
        # Optimize threshold on Val
        calibrated_val_preds = calibrated_model.predict_proba(X_val)[:, 1]
        opt_thresh, min_cost = optimize_threshold(y_val, calibrated_val_preds, cost_matrix)
        
        # Log validation metrics
        mlflow.log_metric("val_auc_pr", compute_metrics(y_val, calibrated_val_preds)['auc_pr'])
        mlflow.log_metric("val_ks", compute_metrics(y_val, calibrated_val_preds)['ks_stat'])
        mlflow.log_metric("optimal_threshold", opt_thresh)
        mlflow.log_metric("val_expected_cost", min_cost)
        
        # Plot calibration curve on Val
        plot_path = "calibration_curve.png"
        plot_calibration_curve_to_file(y_val, calibrated_val_preds, plot_path)
        mlflow.log_artifact(plot_path)
        if os.path.exists(plot_path):
            os.remove(plot_path)
            
        # Final test evaluation
        calibrated_test_preds = calibrated_model.predict_proba(X_test)[:, 1]
        test_cost = compute_expected_cost(y_test, calibrated_test_preds, cost_matrix, opt_thresh)
        mlflow.log_metric("test_expected_cost", test_cost)
        
        # Log model
        mlflow.sklearn.log_model(
            sk_model=calibrated_model, 
            artifact_path="model",
            registered_model_name="credit-risk-model",
            serialization_format=mlflow.sklearn.SERIALIZATION_FORMAT_CLOUDPICKLE
        )
        
        # Generate SHAP background dataset
        import shap
        import joblib
        
        print("Generating SHAP background dataset...")
        X_train_preprocessed = best_model.named_steps['preprocessor'].transform(X_train)
        # Handle sparse matrices returned by preprocessor if any, though ours should be dense
        if hasattr(X_train_preprocessed, "toarray"):
            X_train_preprocessed = X_train_preprocessed.toarray()
            
        background = shap.kmeans(X_train_preprocessed, 100)
        
        bg_path = "shap_background.pkl"
        joblib.dump(background, bg_path)
        mlflow.log_artifact(bg_path)
        if os.path.exists(bg_path):
            os.remove(bg_path)
            
        return run.info.run_id, test_cost

@task
def compare_and_promote(run_id, candidate_cost):
    from mlflow.tracking import MlflowClient
    client = MlflowClient()
    
    model_name = "credit-risk-model"
    
    # Check production model
    try:
        prod_model = client.get_model_version_by_alias(model_name, "Production")
        # In a full setup, we'd fetch prod_cost from tags or re-evaluate. 
        # For this spec, we will promote to Staging unconditionally, 
        # and in reality promotion to Prod is a manual gate anyway.
        # So we just alias as Staging.
        print("Production model exists. Assigning candidate to Staging.")
    except Exception:
        print("No Production model found. Assigning candidate to Staging.")
        
    # We need the latest version to apply the alias
    versions = client.search_model_versions(f"name='{model_name}'")
    latest_version = sorted(versions, key=lambda v: int(v.version))[-1].version
    
    client.set_registered_model_alias(model_name, "Staging", latest_version)
    print(f"Model version {latest_version} aliased as Staging.")

@flow(name="Credit Risk Training Flow")
def run_training_pipeline(config_path: str = "config/training_config.yaml"):
    setup_mlflow()
    
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
        
    df_raw = load_data_task(config)
    df_valid = validate_data_task(df_raw, config)
    df_train_raw, df_val_raw, df_test_raw = split_data_task(df_valid, config)
    df_train, df_val, df_test = build_features_task(df_train_raw, df_val_raw, df_test_raw, config)
    
    run_id, test_cost = train_and_evaluate(df_train, df_val, df_test, config)
    
    print("Waiting for MLflow artifact upload to complete...")
    import time
    time.sleep(30)
    compare_and_promote(run_id, test_cost)

if __name__ == "__main__":
    run_training_pipeline()
