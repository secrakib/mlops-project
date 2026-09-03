import os
import time
import json
import yaml
import requests
import psycopg2
import pandas as pd
import streamlit as st
import concurrent.futures

# Configuration Endpoints
API_URL = os.environ.get("API_URL", "http://api:8000")
PROMETHEUS_URL = os.environ.get("PROMETHEUS_URL", "http://prometheus:9090")
PUSHGATEWAY_URL = os.environ.get("PUSHGATEWAY_URL", "http://pushgateway:9091")
DATABASE_URL = os.environ.get("DATABASE_URL")

st.set_page_config(page_title="Credit Risk Scoring System", page_icon="🏦", layout="wide")

# --- WAKE UP FLOW ---
@st.cache_data(ttl=60)
def check_service(name: str, url_or_dsn: str, check_type: str = "http") -> bool:
    try:
        if check_type == "http":
            resp = requests.get(url_or_dsn, timeout=5)
            return resp.status_code in [200, 202]
        elif check_type == "postgres":
            conn = psycopg2.connect(url_or_dsn, connect_timeout=5)
            conn.close()
            return True
    except Exception:
        return False
    return False

def wake_up_services():
    services = {
        "FastAPI Server": {"url": f"{API_URL}/health", "type": "http"},
        "Prometheus": {"url": f"{PROMETHEUS_URL}/-/healthy", "type": "http"},
        "Pushgateway": {"url": f"{PUSHGATEWAY_URL}/-/healthy", "type": "http"},
        "Supabase DB": {"url": DATABASE_URL, "type": "postgres"},
    }
    
    status_placeholders = {name: st.empty() for name in services.keys()}
    all_awake = False
    
    with st.spinner("Waking up infrastructure... (This might take a minute on Render's free tier)"):
        while not all_awake:
            results = {}
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = {
                    executor.submit(check_service, name, svc["url"], svc["type"]): name
                    for name, svc in services.items()
                }
                for future in concurrent.futures.as_completed(futures):
                    name = futures[future]
                    results[name] = future.result()
            
            all_awake = all(results.values())
            for name, is_up in results.items():
                if is_up:
                    status_placeholders[name].success(f"{name}: Awake ✅")
                else:
                    status_placeholders[name].warning(f"{name}: Waking up... ⏳")
            
            if not all_awake:
                time.sleep(3)
                
    st.success("All systems are online and ready!")
    time.sleep(1)
    
# --- LOAD CONFIG ---
@st.cache_data
def load_features():
    with open("config/training_config.yaml", "r") as f:
        cfg = yaml.safe_load(f)
    return cfg["features"]["selected_numeric_features"]

# --- UI LOGIC ---
def main():
    st.title("🏦 Credit Risk Scoring System")
    st.markdown("Predict the probability of loan default and receive a business-cost-driven decision.")
    
    # Initialize wake-up
    if "systems_awake" not in st.session_state:
        wake_up_services()
        st.session_state["systems_awake"] = True

    features = load_features()
    
    # Personas
    st.sidebar.header("Applicant Persona")
    persona = st.sidebar.selectbox("Select a predefined profile:", ["Low Risk Profile", "High Risk Profile", "Custom"])
    
    # Create base dictionary
    payload_dict = {f: 0.0 for f in features}
    
    if persona == "Low Risk Profile":
        payload_dict.update({
            "loan_amnt": 5000.0,
            "int_rate": 0.05,
            "annual_inc": 120000.0,
            "fico_range_low": 750.0,
            "fico_range_high": 754.0,
            "dti": 10.0,
            "revol_util": 0.2
        })
    elif persona == "High Risk Profile":
        payload_dict.update({
            "loan_amnt": 35000.0,
            "int_rate": 0.25,
            "annual_inc": 45000.0,
            "fico_range_low": 600.0,
            "fico_range_high": 604.0,
            "dti": 35.0,
            "revol_util": 0.95
        })
        
    st.subheader("Applicant Data (JSON)")
    user_json = st.text_area("Edit feature values directly:", value=json.dumps(payload_dict, indent=2), height=300)
    
    if st.button("Score Applicant", type="primary", use_container_width=True):
        try:
            req_data = json.loads(user_json)
        except json.JSONDecodeError:
            st.error("Invalid JSON format.")
            return
            
        with st.spinner("Scoring and calculating SHAP values..."):
            try:
                resp = requests.post(f"{API_URL}/score", json=req_data)
                resp.raise_for_status()
                data = resp.json()
                
                col1, col2, col3 = st.columns(3)
                
                # Display Results
                prob = data["probability"]
                decision = data["decision"]
                req_id = data["request_id"]
                
                col1.metric("Probability of Default", f"{prob:.1%}")
                
                # Color code decision
                if decision == "Approve":
                    col2.success(f"Decision: {decision}")
                else:
                    col2.error(f"Decision: {decision}")
                    
                col3.info(f"Request ID:\n{req_id[:8]}...")
                
                st.divider()
                st.subheader("Model Explanation (SHAP Values)")
                st.markdown("Features contributing to **pushing the probability of default higher** (positive values) vs **lower** (negative values).")
                
                shap_vals = data["shap_values"]
                # Convert to dataframe for plotting
                # Sort by absolute magnitude to show top features
                df_shap = pd.DataFrame(list(shap_vals.items()), columns=["Feature", "SHAP Value"])
                df_shap["abs_val"] = df_shap["SHAP Value"].abs()
                df_shap = df_shap.sort_values(by="abs_val", ascending=False).head(15) # Top 15
                
                st.bar_chart(df_shap.set_index("Feature")["SHAP Value"])
                
            except requests.exceptions.RequestException as e:
                st.error(f"API Request Failed: {e}")

if __name__ == "__main__":
    main()
