import pandas as pd
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier
from sklearn.model_selection import RandomizedSearchCV
from sklearn.pipeline import Pipeline

def train_logistic_regression(X_train: pd.DataFrame, y_train: pd.Series, preprocessor) -> Pipeline:
    """Trains a baseline Logistic Regression model wrapped in a Pipeline."""
    print("Training LogisticRegression...")
    model = LogisticRegression(class_weight='balanced', max_iter=1000)
    pipeline = Pipeline(steps=[('preprocessor', preprocessor), ('classifier', model)])
    pipeline.fit(X_train, y_train)
    return pipeline

def train_xgboost(X_train: pd.DataFrame, y_train: pd.Series, param_grid: dict, preprocessor, n_iter: int = 8) -> Pipeline:
    """Trains an XGBoost model using RandomizedSearchCV for hyperparameter tuning over the Pipeline."""
    print(f"Training XGBoost with random search over grid: {param_grid}...")
    
    xgb = XGBClassifier(
        objective='binary:logistic',
        tree_method='hist',
        scale_pos_weight=(len(y_train) - sum(y_train)) / sum(y_train),  # rough class weight
        eval_metric='logloss',
        n_jobs=-1,
        random_state=42
    )
    
    pipeline = Pipeline(steps=[('preprocessor', preprocessor), ('classifier', xgb)])
    
    # Prefix parameters to correctly target the classifier within the pipeline
    prefixed_param_grid = {f'classifier__{k}': v for k, v in param_grid.items()}
    
    # Calculate effective iterations: cannot sample more than total combinations
    total_combinations = 1
    for v in param_grid.values():
        total_combinations *= len(v) if isinstance(v, list) else 1
    effective_n_iter = min(n_iter, total_combinations)
    
    random_search = RandomizedSearchCV(
        estimator=pipeline,
        param_distributions=prefixed_param_grid,
        n_iter=effective_n_iter,
        scoring='average_precision',
        cv=3,
        random_state=42,
        n_jobs=1,
        verbose=1
    )
    
    random_search.fit(X_train, y_train)
    print(f"Best parameters found: {random_search.best_params_}")
    
    return random_search.best_estimator_
