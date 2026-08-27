import pandas as pd
import numpy as np

def load_data(path: str) -> pd.DataFrame:
    """Loads the dataset from the given path."""
    return pd.read_csv(path)

def temporal_split(df: pd.DataFrame, val_ratio: float = 0.15, test_ratio: float = 0.15):
    """
    Splits the dataframe temporally based on issue_d using given ratios.
    Assumes issue_d can be parsed as a datetime.
    """
    if 'issue_d' not in df.columns:
        raise ValueError("issue_d column not found for temporal split")
        
    df['issue_d'] = pd.to_datetime(df['issue_d'])
    
    # Sort chronologically to maintain Out-Of-Time validation
    df = df.sort_values('issue_d').reset_index(drop=True)
    
    n = len(df)
    train_end = int(n * (1 - val_ratio - test_ratio))
    val_end = int(n * (1 - test_ratio))
    
    df_train = df.iloc[:train_end].copy()
    df_val = df.iloc[train_end:val_end].copy()
    df_test = df.iloc[val_end:].copy()
    
    return df_train, df_val, df_test

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
