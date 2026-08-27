import pandas as pd
import numpy as np

def load_data(path: str) -> pd.DataFrame:
    """Loads the dataset from the given path."""
    return pd.read_csv(path)

def temporal_split(df: pd.DataFrame, val_start: str, test_start: str):
    """
    Splits the dataframe temporally based on issue_d.
    Assumes issue_d can be parsed as a datetime.
    """
    if 'issue_d' not in df.columns:
        raise ValueError("issue_d column not found for temporal split")
        
    df['issue_d'] = pd.to_datetime(df['issue_d'])
    
    train_mask = df['issue_d'] < val_start
    val_mask = (df['issue_d'] >= val_start) & (df['issue_d'] < test_start)
    test_mask = df['issue_d'] >= test_start
    
    return df[train_mask].copy(), df[val_mask].copy(), df[test_mask].copy()

def build_features(df: pd.DataFrame, target_col: str, leakage_cols: list) -> pd.DataFrame:
    """
    Preprocesses the dataframe by creating the target,
    dropping leakage/identifier columns, and selecting numeric features.
    Also handles basic imputation.
    """
    df = df.copy()
    
    # Handle target if present
    if target_col in df.columns:
        # Assuming target_col is already 0/1 based on spec, but let's be safe
        df = df[df[target_col].isin([0, 1])]
        df['target'] = df[target_col].astype(int)
    
    # Drop leakage columns
    df = df.drop(columns=leakage_cols, errors='ignore')
    
    # Drop identifiers and textual columns that aren't useful raw
    identifiers = ['id', 'member_id', target_col, 'issue_d', 'target']
    
    # Select numeric features
    numeric_df = df.select_dtypes(include=['float64', 'int64']).drop(columns=identifiers, errors='ignore')
    
    # Basic imputation (fill NaNs with 0)
    numeric_df = numeric_df.fillna(0)
    
    if 'target' in df.columns:
        numeric_df['target'] = df['target']
        
    return numeric_df
