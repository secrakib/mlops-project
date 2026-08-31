import pandas as pd
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import Pipeline

def train_logistic_regression(X_train: pd.DataFrame, y_train: pd.Series, preprocessor) -> Pipeline:
    """Trains a baseline Logistic Regression model wrapped in a Pipeline."""
    print("Training LogisticRegression...")
    model = LogisticRegression(class_weight='balanced', max_iter=2000)
    pipeline = Pipeline(steps=[('preprocessor', preprocessor), ('classifier', model)])
    pipeline.fit(X_train, y_train)
    return pipeline

def train_xgboost(X_train: pd.DataFrame, y_train: pd.Series, param_grid: dict, preprocessor) -> Pipeline:
    """Trains an XGBoost model using GridSearchCV for hyperparameter tuning over the Pipeline."""
    print(f"Training XGBoost with grid: {param_grid}...")
    
    xgb = XGBClassifier(
        objective='binary:logistic',
        tree_method='hist',
        scale_pos_weight=(len(y_train) - sum(y_train)) / sum(y_train),  # rough class weight
        eval_metric='logloss'
    )
    
    pipeline = Pipeline(steps=[('preprocessor', preprocessor), ('classifier', xgb)])
    
    # Prefix parameters to correctly target the classifier within the pipeline
    prefixed_param_grid = {f'classifier__{k}': v for k, v in param_grid.items()}
    
    grid_search = GridSearchCV(
        estimator=pipeline,
        param_grid=prefixed_param_grid,
        scoring='average_precision',
        cv=3,
        n_jobs=-1,
        verbose=1
    )
    
    grid_search.fit(X_train, y_train)
    print(f"Best parameters found: {grid_search.best_params_}")
    
    return grid_search.best_estimator_
