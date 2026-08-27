import pandas as pd
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier
from sklearn.model_selection import GridSearchCV

def train_logistic_regression(X_train: pd.DataFrame, y_train: pd.Series) -> LogisticRegression:
    """Trains a baseline Logistic Regression model."""
    print("Training LogisticRegression...")
    model = LogisticRegression(class_weight='balanced', max_iter=2000)
    model.fit(X_train, y_train)
    return model

def train_xgboost(X_train: pd.DataFrame, y_train: pd.Series, param_grid: dict) -> XGBClassifier:
    """Trains an XGBoost model using GridSearchCV for hyperparameter tuning."""
    print(f"Training XGBoost with grid: {param_grid}...")
    
    xgb = XGBClassifier(
        objective='binary:logistic',
        tree_method='hist',
        scale_pos_weight=(len(y_train) - sum(y_train)) / sum(y_train),  # rough class weight
        eval_metric='logloss',
        use_label_encoder=False
    )
    
    grid_search = GridSearchCV(
        estimator=xgb,
        param_grid=param_grid,
        scoring='average_precision',
        cv=3,
        n_jobs=-1,
        verbose=1
    )
    
    grid_search.fit(X_train, y_train)
    print(f"Best parameters found: {grid_search.best_params_}")
    
    return grid_search.best_estimator_
