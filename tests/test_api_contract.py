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

def test_score_endpoint_shap_values_not_empty(client):
    """Test that SHAP values are not empty when scoring a valid payload."""
    payload = {
      "loan_amnt": 15000,
      "funded_amnt": 15000,
      "funded_amnt_inv": 15000,
      "int_rate": 11.44,
      "installment": 493.82,
      "annual_inc": 72000,
      "dti": 18.5,
      "delinq_2yrs": 0,
      "fico_range_low": 690,
      "fico_range_high": 694,
      "inq_last_6mths": 1,
      "open_acc": 11,
      "pub_rec": 0,
      "revol_bal": 12500,
      "revol_util": 45.2,
      "total_acc": 22,
      "collections_12_mths_ex_med": 0,
      "acc_now_delinq": 0,
      "tot_coll_amt": 150,
      "tot_cur_bal": 145000,
      "open_acc_6m": 2,
      "open_act_il": 3,
      "open_il_12m": 1,
      "open_il_24m": 2,
      "mths_since_rcnt_il": 8,
      "total_bal_il": 28000,
      "il_util": 68.5,
      "open_rv_12m": 2,
      "open_rv_24m": 4,
      "max_bal_bc": 4200,
      "all_util": 54.1,
      "total_rev_hi_lim": 27600,
      "inq_fi": 1,
      "total_cu_tl": 2,
      "inq_last_12m": 3,
      "acc_open_past_24mths": 6,
      "avg_cur_bal": 13182,
      "bc_open_to_buy": 11200,
      "bc_util": 51.3,
      "chargeoff_within_12_mths": 0,
      "delinq_amnt": 0,
      "mo_sin_old_il_acct": 118,
      "mo_sin_old_rev_tl_op": 145,
      "mo_sin_rcnt_rev_tl_op": 5,
      "mo_sin_rcnt_tl": 5,
      "mort_acc": 1,
      "mths_since_recent_bc": 5,
      "mths_since_recent_inq": 4,
      "num_accts_ever_120_pd": 0,
      "num_actv_bc_tl": 4,
      "num_actv_rev_tl": 6,
      "num_bc_sats": 5,
      "num_bc_tl": 8,
      "num_il_tl": 7,
      "num_op_rev_tl": 9,
      "num_rev_accts": 14,
      "num_rev_tl_bal_gt_0": 6,
      "num_sats": 11,
      "num_tl_120dpd_2m": 0,
      "num_tl_30dpd": 0,
      "num_tl_90g_dpd_24m": 0,
      "num_tl_op_past_12m": 3,
      "pct_tl_nvr_dlq": 100,
      "percent_bc_gt_75": 25.0,
      "pub_rec_bankruptcies": 0,
      "tax_liens": 0,
      "tot_hi_cred_lim": 185000,
      "total_bal_ex_mort": 40500,
      "total_bc_limit": 23000,
      "total_il_high_credit_limit": 31000,
      "months_since_earliest_cr_line": 180
    }
    
    response = client.post("/score", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["shap_values"]) > 0, "SHAP values should not be empty"

