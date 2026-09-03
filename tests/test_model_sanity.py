import os
import pytest
import pandas as pd
import numpy as np
import mlflow
from src.serving.config import load_serving_config, load_training_config, settings

@pytest.fixture(scope="module")
def mlflow_model():
    """
    Downloads the actual model artifact from MLflow to run real sanity checks.
    Requires DAGSHUB_TOKEN to be set in environment (via .env or GitHub Secrets).
    """
    # Ensure tracking URI and auth are set
    os.environ["MLFLOW_TRACKING_USERNAME"] = settings.DAGSHUB_USER
    if settings.DAGSHUB_TOKEN:
        os.environ["MLFLOW_TRACKING_PASSWORD"] = settings.DAGSHUB_TOKEN
        
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    
    serving_cfg = load_serving_config()
    model_uri = f"models:/{serving_cfg['model_name']}@{settings.MODEL_ALIAS}"
    
    try:
        model = mlflow.sklearn.load_model(model_uri)
        return model
    except Exception as e:
        pytest.skip(f"Could not load MLflow model from {model_uri}. Ensure DAGSHUB_TOKEN is valid. Error: {e}")

@pytest.fixture(scope="module")
def numeric_features():
    training_cfg = load_training_config()
    return training_cfg['features']['selected_numeric_features']

def test_model_probability_bounds(mlflow_model, numeric_features):
    """
    Ensures that the model outputs a valid probability (between 0.0 and 1.0)
    for extreme dummy inputs.
    """
    # Create extreme dummy inputs (all zeros, and all very large numbers)
    df_zeros = pd.DataFrame(np.zeros((1, len(numeric_features))), columns=numeric_features)
    df_large = pd.DataFrame(np.ones((1, len(numeric_features))) * 1e6, columns=numeric_features)
    
    # Predict
    prob_zeros = mlflow_model.predict_proba(df_zeros)[0][1]
    prob_large = mlflow_model.predict_proba(df_large)[0][1]
    
    # Assert bounds
    assert 0.0 <= prob_zeros <= 1.0, f"Probability {prob_zeros} is out of bounds!"
    assert 0.0 <= prob_large <= 1.0, f"Probability {prob_large} is out of bounds!"

def test_model_input_schema_matching(mlflow_model, numeric_features):
    """
    Ensures the model can predict on a dataframe structured exactly as 
    defined in the training config's numeric_features list.
    """
    df_valid = pd.DataFrame(np.random.rand(10, len(numeric_features)), columns=numeric_features)
    
    # This should not raise any feature name mismatch errors
    preds = mlflow_model.predict_proba(df_valid)
    assert preds.shape == (10, 2)
