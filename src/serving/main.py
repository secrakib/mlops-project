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

logger = setup_prediction_logger(db_url=settings.DATABASE_URL)

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    logger.info("Initializing Supabase Database schema...")
    init_db(settings.DATABASE_URL)
    
    logger.info("Loading configurations...")
    app.state.serving_cfg = load_serving_config()
    app.state.training_cfg = load_training_config()
    app.state.cost_matrix = app.state.training_cfg["evaluation"]["cost_matrix"]
    
    # Configure MLflow auth (needed to pull model & SHAP artifacts)
    os.environ["MLFLOW_TRACKING_USERNAME"] = settings.DAGSHUB_USER
    os.environ["MLFLOW_TRACKING_PASSWORD"] = settings.DAGSHUB_TOKEN
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    
    # Load MLflow Model
    model_uri = f"models:/{app.state.serving_cfg['model_name']}@{settings.MODEL_ALIAS}"
    logger.info(f"Loading MLflow model: {model_uri}")
    app.state.mlflow_model = mlflow.sklearn.load_model(model_uri)
    
    try:
        base_model = app.state.mlflow_model
        if type(base_model).__name__ == 'CalibratedClassifierCV':
            if hasattr(base_model, 'calibrated_classifiers_') and len(base_model.calibrated_classifiers_) > 0:
                base_model = base_model.calibrated_classifiers_[0].estimator
            else:
                base_model = base_model.estimator
            if type(base_model).__name__ == 'FrozenEstimator':
                base_model = getattr(base_model, 'estimator', base_model)
                
        model_step = base_model.steps[-1][1]
        model_type = type(model_step).__name__
        logger.info(f"Loaded model type: {model_type}")
        
        if model_type == 'XGBClassifier':
            app.state.is_tree = True
            app.state.shap_explainer = shap.TreeExplainer(model_step)
            app.state.preprocessor = base_model.steps[0][1]
            logger.info("Initialized SHAP TreeExplainer.")
        else:
            app.state.is_tree = False
            logger.info("Resolving MLflow run to fetch SHAP background...")
            client = mlflow.tracking.MlflowClient()
            model_version = client.get_model_version_by_alias(app.state.serving_cfg['model_name'], settings.MODEL_ALIAS)
            
            import joblib
            shap_bg_path = client.download_artifacts(model_version.run_id, "shap_background.pkl")
            shap_background = joblib.load(shap_bg_path)
                
            logger.info("Initializing SHAP KernelExplainer...")
            def predict_fn(X):
                import pandas as pd
                cols = app.state.training_cfg['features']['selected_numeric_features']
                df_x = pd.DataFrame(X, columns=cols)
                return app.state.mlflow_model.predict_proba(df_x)
                
            app.state.shap_explainer = shap.KernelExplainer(predict_fn, shap_background)
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Failed to load SHAP artifact or explainer: {e}")
        app.state.shap_explainer = None # We will just return empty dict if this fails
        
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
def health_check(request: Request):
    """Liveness probe. Essential for Render cold starts and monitoring."""
    if not getattr(request.app.state, 'mlflow_model', None):
        raise HTTPException(status_code=503, detail="Model not loaded yet.")
    return {"status": "ok", "model_loaded": True}

@app.post("/score", response_model=ScoreResponse)
def score(request: Request, payload: ScoreRequest):
    """Predicts default probability and returns SHAP values."""
    from src.common.logging_config import request_id_var
    req_id = request_id_var.get()
    
    mlflow_model = request.app.state.mlflow_model
    cost_matrix = request.app.state.cost_matrix
    shap_explainer = request.app.state.shap_explainer
    training_cfg = request.app.state.training_cfg
    is_tree = getattr(request.app.state, 'is_tree', False)
    
    # 1. Convert to DataFrame (respects order of Pydantic model)
    data_dict = payload.model_dump()
    df = pd.DataFrame([data_dict])
    
    # 2. Predict Probability (Class 1 = Default)
    proba = float(mlflow_model.predict_proba(df)[0][1])
    
    # 3. Decision Logic (Cost-Matrix Threshold)
    threshold = cost_matrix["fp_cost"] / (cost_matrix["fp_cost"] + cost_matrix["fn_cost"])
    decision = "Reject" if proba >= threshold else "Approve"
    
    # 4. SHAP Explanations
    feat_shap_dict = {}
    if shap_explainer:
        import numpy as np
        if is_tree:
            preprocessor = request.app.state.preprocessor
            transformed_data = preprocessor.transform(df)
            shap_vals = shap_explainer.shap_values(transformed_data)
            # For XGBoost binary classification, shap_vals is typically (n_samples, n_features)
            class_1_shap = np.array(shap_vals).flatten()
        else:
            shap_vals = shap_explainer.shap_values(df, silent=True)
            class_1_shap = shap_vals[1][0] if isinstance(shap_vals, list) else shap_vals[0]
            class_1_shap = np.array(class_1_shap).flatten()
            
        cols = training_cfg['features']['selected_numeric_features']
        feat_shap_dict = dict(zip(cols, [float(x) for x in class_1_shap]))
        
    # 5. Central Logging (stdout + Supabase Postgres)
    log_payload = {
        "request_json": data_dict,
        "probability": proba,
        "decision": decision,
        "model_version": settings.MODEL_ALIAS
    }
    # This automatically includes the request_id thanks to our RequestIdFilter
    logger.info(log_payload)
    
    return ScoreResponse(
        probability=proba,
        decision=decision,
        shap_values=feat_shap_dict,
        request_id=req_id
    )
