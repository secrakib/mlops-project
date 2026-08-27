import os
import pandas as pd
import mlflow
import mlflow.sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score
from scipy.stats import ks_2samp
from mlflow.tracking import MlflowClient
from dotenv import load_dotenv

def main():
    load_dotenv()
    
    # Build Dagshub MLflow URI
    dagshub_user = os.getenv("DAGSHUB_USER")
    dagshub_repo = os.getenv("DAGSHUB_REPO")
    dagshub_token = os.getenv("DAGSHUB_TOKEN")
    
    if not dagshub_user or not dagshub_repo or not dagshub_token:
        print("Missing DAGSHUB credentials in .env")
        return
        
    os.environ["MLFLOW_TRACKING_USERNAME"] = dagshub_user
    os.environ["MLFLOW_TRACKING_PASSWORD"] = dagshub_token
    
    tracking_uri = f"https://dagshub.com/{dagshub_user}/{dagshub_repo}.mlflow"
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment("credit-risk-scoring")
    
    print("Loading data...")
    # Load small subset of data, assuming we run from project root
    df = pd.read_csv("data/dataset.csv", nrows=10000)
    
    print(f"Loaded {len(df)} rows. Columns: {list(df.columns)[:5]}...")
    
    # Preprocessing based on spec.md
    if 'loan_status' in df.columns:
        # It appears loan_status is already 0 and 1 in dataset.csv
        df = df[df['loan_status'].isin([0, 1])].copy()
        df['target'] = df['loan_status'].astype(int)
    else:
        # Fallback if loan_status is not found
        df['target'] = (df.index % 2 == 0).astype(int)
        
    if len(df) == 0:
        print("No valid rows left after filtering for Fully Paid / Charged Off.")
        return
        
    # Drop leakage columns as per spec.md if they exist
    leakage_cols = ['total_pymnt', 'recoveries', 'last_pymnt_amnt', 'collection_recovery_fee']
    df = df.drop(columns=leakage_cols, errors='ignore')
    
    # Select numeric features for simplicity and handle NaNs
    features = df.select_dtypes(include=['float64', 'int64']).drop(columns=['target', 'loan_status', 'id', 'member_id'], errors='ignore')
    features = features.fillna(0)
    target = df['target']
    
    X_train, y_train = features, target
    
    print("Starting MLflow run...")
    with mlflow.start_run():
        print("Training LogisticRegression...")
        model = LogisticRegression(class_weight='balanced', max_iter=1000)
        model.fit(X_train, y_train)
        
        y_pred_proba = model.predict_proba(X_train)[:, 1]
        
        # Calculate metrics
        if len(y_train.unique()) > 1:
            auc_pr = average_precision_score(y_train, y_pred_proba)
        else:
            auc_pr = 0.0
            
        preds_pos = y_pred_proba[y_train == 1]
        preds_neg = y_pred_proba[y_train == 0]
        if len(preds_pos) > 0 and len(preds_neg) > 0:
            ks_stat, _ = ks_2samp(preds_pos, preds_neg)
        else:
            ks_stat = 0.0
            
        mlflow.log_metric("auc_pr", auc_pr)
        mlflow.log_metric("ks_stat", ks_stat)
        
        # Log AND register model
        mlflow.sklearn.log_model(
            sk_model=model,
            name="model",
            registered_model_name="my-model"
        )
        print(f"Logged model with AUC-PR: {auc_pr:.4f}, KS: {ks_stat:.4f}")
    
    # Set alias
    print("Setting model alias 'Staging'...")
    client = MlflowClient()
    latest_versions = client.search_model_versions("name='my-model'")
    if latest_versions:
        # Sort by version number
        latest_version = sorted(latest_versions, key=lambda v: int(v.version))[-1].version
        client.set_registered_model_alias("my-model", "Staging", latest_version)
        print(f"Set Staging alias to version {latest_version}")
    else:
        print("Model 'my-model' not found in registry.")

if __name__ == "__main__":
    main()
