import pytest
from fastapi.testclient import TestClient
from src.serving.main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_health_endpoint(client):
    """Test that the health endpoint returns 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "model_loaded": True}

def test_score_endpoint_422_on_empty_payload(client):
    """Test that sending an empty payload returns a 422 Validation Error."""
    response = client.post("/score", json={})
    assert response.status_code == 422

def test_score_endpoint_422_on_missing_feature(client):
    """Test that missing even one feature triggers a 422."""
    # We load the training config to get the required features
    from src.serving.config import load_training_config
    features = load_training_config()["features"]["selected_numeric_features"]
    
    # Create a payload missing the very first feature
    payload = {feat: 0.0 for feat in features[1:]}
    
    response = client.post("/score", json=payload)
    assert response.status_code == 422
    assert "Field required" in response.text

def test_score_endpoint_success(client):
    """Test that a fully valid payload returns a 200 OK with the expected schema."""
    from src.serving.config import load_training_config
    features = load_training_config()["features"]["selected_numeric_features"]
    
    # Create a valid payload with dummy 0.0 values
    payload = {feat: 0.0 for feat in features}
    
    response = client.post("/score", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "probability" in data
    assert "decision" in data
    assert "shap_values" in data
    assert "request_id" in data
