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

import pandera as pa
from pandera import Column, DataFrameSchema
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

def get_pandera_schema(config: dict, is_inference: bool = False) -> pa.DataFrameSchema:
    """Dynamically builds a Pandera schema based on the config."""
    columns = {}
    
    numeric_features = config['features']['selected_numeric_features']
    for feature in numeric_features:
        # Numeric features coerced to float, nullable as Imputer handles NaNs
        columns[feature] = Column(float, coerce=True, nullable=True)
        
    if not is_inference:
        target_col = config['data']['target_col']
        # Don't strictly check type for target/date to avoid parsing errors, just ensure presence
        columns[target_col] = Column(coerce=False, nullable=True)
        columns['issue_d'] = Column(coerce=False, nullable=True)
        
    return DataFrameSchema(columns=columns, strict='filter')

def build_features(df: pd.DataFrame, config: dict, is_inference: bool = False) -> pd.DataFrame:
    """
    Preprocesses the dataframe by validating with Pandera, creating the target,
    and dropping unnecessary columns.
    """
    df = df.copy()
    
    # 1. Validate and filter columns
    schema = get_pandera_schema(config, is_inference=is_inference)
    df = schema.validate(df)
    
    # 2. Handle target
    if not is_inference:
        target_col = config['data']['target_col']
        if target_col in df.columns:
            # Keep only valid binary targets and convert
            df = df[df[target_col].isin([0, 1, '0', '1', 0.0, 1.0])]
            df['target'] = df[target_col].astype(int)
            # Drop the original target and issue_d which is no longer needed after split
            df = df.drop(columns=[target_col, 'issue_d'], errors='ignore')
            
    return df

def create_preprocessor(numeric_features: list) -> ColumnTransformer:
    """Creates a scikit-learn preprocessor pipeline."""
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_features)
        ],
        remainder='drop'
    )
    return preprocessor
