import pandas as pd
import numpy as np
import pytest
from src.features.feature_pipeline import temporal_split, build_features, create_preprocessor

@pytest.fixture
def dummy_config():
    return {
        'data': {
            'target_col': 'loan_status'
        },
        'features': {
            'selected_numeric_features': ['loan_amnt', 'int_rate', 'annual_inc']
        }
    }

def test_temporal_split():
    # Create dummy data spanning multiple dates
    df = pd.DataFrame({
        'issue_d': ['2016-01-01', '2016-02-01', '2016-03-01', '2016-04-01', '2016-05-01'],
        'val': [1, 2, 3, 4, 5]
    })
    
    # Ratios 0.2 and 0.2 means 60% train (3), 20% val (1), 20% test (1)
    df_train, df_val, df_test = temporal_split(df, val_ratio=0.2, test_ratio=0.2)
    
    assert len(df_train) == 3
    assert len(df_val) == 1
    assert len(df_test) == 1
    
    # Check that they are ordered chronologically
    assert df_train['val'].tolist() == [1, 2, 3]
    assert df_val['val'].tolist() == [4]
    assert df_test['val'].tolist() == [5]

def test_temporal_split_missing_col():
    df = pd.DataFrame({'val': [1, 2, 3]})
    with pytest.raises(ValueError, match="issue_d column not found"):
        temporal_split(df)

def test_build_features_inference(dummy_config):
    # Data with extra columns, nulls, and no target
    df = pd.DataFrame({
        'loan_amnt': [1000.0, np.nan, 3000.0],
        'int_rate': [0.1, 0.2, 0.3],
        'annual_inc': [50000.0, 60000.0, 70000.0],
        'extra_col': ['drop_me', 'drop_me_too', 'and_me']
    })
    
    df_out = build_features(df, dummy_config, is_inference=True)
    
    # Should only keep the selected numeric features (strict filter)
    assert list(df_out.columns) == dummy_config['features']['selected_numeric_features']
    # Null should be preserved (imputer handles it later)
    assert pd.isna(df_out.iloc[1]['loan_amnt'])

def test_build_features_training(dummy_config):
    df = pd.DataFrame({
        'loan_amnt': [1000.0, 2000.0],
        'int_rate': [0.1, 0.2],
        'annual_inc': [50000.0, 60000.0],
        'loan_status': [1, 0],  # Valid targets
        'issue_d': ['2016-01-01', '2016-02-01']
    })
    
    df_out = build_features(df, dummy_config, is_inference=False)
    
    # Should keep numeric features + 'target', should drop 'loan_status' and 'issue_d'
    expected_cols = dummy_config['features']['selected_numeric_features'] + ['target']
    assert set(df_out.columns) == set(expected_cols)
    assert df_out['target'].tolist() == [1, 0]

def test_build_features_training_invalid_target(dummy_config):
    # Tests that invalid targets (like 'pending') are dropped
    df = pd.DataFrame({
        'loan_amnt': [1000.0, 2000.0, 3000.0],
        'int_rate': [0.1, 0.2, 0.3],
        'annual_inc': [50000.0, 60000.0, 70000.0],
        'loan_status': [1, 'pending', 0], 
        'issue_d': ['2016-01-01', '2016-02-01', '2016-03-01']
    })
    
    df_out = build_features(df, dummy_config, is_inference=False)
    
    # The row with 'pending' should be dropped
    assert len(df_out) == 2
    assert df_out['target'].tolist() == [1, 0]
