from pydantic import BaseModel, create_model
from typing import Dict, Any, Optional
from src.serving.config import load_training_config

# Load training config to dynamically build the required feature schema
training_config = load_training_config()
numeric_features = training_config["features"]["selected_numeric_features"]

# Dynamically construct fields for Pydantic BaseModel. 
# This enforces that the API request MUST contain exactly the 77 numeric features.
# By setting `(float, ...)`, we make each field required and strongly typed.
request_fields = {feat: (float, ...) for feat in numeric_features}

# Create the ScoreRequest Pydantic model at runtime
ScoreRequest = create_model('ScoreRequest', **request_fields)

class ScoreResponse(BaseModel):
    probability: float
    decision: str
    shap_values: Dict[str, float]
    request_id: str
