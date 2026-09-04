import pytest
from fastapi.testclient import TestClient
from src.serving.main import app
import os
import requests

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_integration_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_integration_score_endpoint_success(client):
    """Test the scoring endpoint end-to-end including SHAP and DB Logging."""
    # A valid payload
    payload = {
        "loan_amnt": 10000,
        "funded_amnt": 10000,
        "funded_amnt_inv": 10000,
        "int_rate": 10.99,
        "installment": 327.34,
        "annual_inc": 65000,
        "dti": 15.0,
        "delinq_2yrs": 0,
        "fico_range_low": 700,
        "fico_range_high": 704,
        "inq_last_6mths": 0,
        "open_acc": 10,
        "pub_rec": 0,
        "revol_bal": 15000,
        "revol_util": 50.0,
        "total_acc": 20,
        "collections_12_mths_ex_med": 0,
        "acc_now_delinq": 0,
        "tot_coll_amt": 0,
        "tot_cur_bal": 120000,
        "open_acc_6m": 1,
        "open_act_il": 2,
        "open_il_12m": 0,
        "open_il_24m": 1,
        "mths_since_rcnt_il": 12,
        "total_bal_il": 20000,
        "il_util": 60.0,
        "open_rv_12m": 1,
        "open_rv_24m": 2,
        "max_bal_bc": 5000,
        "all_util": 55.0,
        "total_rev_hi_lim": 30000,
        "inq_fi": 0,
        "total_cu_tl": 1,
        "inq_last_12m": 2,
        "acc_open_past_24mths": 3,
        "avg_cur_bal": 12000,
        "bc_open_to_buy": 15000,
        "bc_util": 50.0,
        "chargeoff_within_12_mths": 0,
        "delinq_amnt": 0,
        "mo_sin_old_il_acct": 100,
        "mo_sin_old_rev_tl_op": 120,
        "mo_sin_rcnt_rev_tl_op": 10,
        "mo_sin_rcnt_tl": 10,
        "mort_acc": 1,
        "mths_since_recent_bc": 10,
        "mths_since_recent_inq": 6,
        "num_accts_ever_120_pd": 0,
        "num_actv_bc_tl": 3,
        "num_actv_rev_tl": 5,
        "num_bc_sats": 4,
        "num_bc_tl": 6,
        "num_il_tl": 5,
        "num_op_rev_tl": 8,
        "num_rev_accts": 12,
        "num_rev_tl_bal_gt_0": 5,
        "num_sats": 10,
        "num_tl_120dpd_2m": 0,
        "num_tl_30dpd": 0,
        "num_tl_90g_dpd_24m": 0,
        "num_tl_op_past_12m": 2,
        "pct_tl_nvr_dlq": 100.0,
        "percent_bc_gt_75": 25.0,
        "pub_rec_bankruptcies": 0,
        "tax_liens": 0,
        "tot_hi_cred_lim": 150000,
        "total_bal_ex_mort": 35000,
        "total_bc_limit": 30000,
        "total_il_high_credit_limit": 25000,
        "months_since_earliest_cr_line": 150
    }

    response = client.post("/score", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "probability" in data
    assert "decision" in data
    assert "shap_values" in data
    
    # SHAP values should exist
    assert len(data["shap_values"]) > 0

    # Test Prometheus metrics
    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200
    assert "http_requests_total" in metrics_response.text
