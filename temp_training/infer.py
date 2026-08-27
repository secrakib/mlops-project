import os
import pandas as pd
import mlflow.pyfunc
from dotenv import load_dotenv

def main():
    load_dotenv()
    
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
    
    # Load model from registry
    model_uri = "models:/my-model@Staging"
    print(f"Loading model from {model_uri} ...")
    model = mlflow.pyfunc.load_model(model_uri)
    print("Model loaded successfully!")
    
    # Load dummy input data matching features (skip target/id columns)
    print("Loading test features...")
    df = pd.read_csv("data/dataset.csv", nrows=10)
    
    leakage_cols = ['total_pymnt', 'recoveries', 'last_pymnt_amnt', 'collection_recovery_fee']
    df = df.drop(columns=leakage_cols, errors='ignore')
    
    features = df.select_dtypes(include=['float64', 'int64']).drop(columns=['loan_status', 'id', 'member_id'], errors='ignore')
    features = features.fillna(0)
    
    print("Running predictions...")
    predictions = model.predict(features)
    print("Predictions for the first 10 rows:")
    print(predictions)

if __name__ == "__main__":
    main()
