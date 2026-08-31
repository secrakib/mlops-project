import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.metrics import average_precision_score, precision_recall_curve
from scipy.stats import ks_2samp
import os
try:
    from sklearn.calibration import FrozenEstimator
except ImportError:
    FrozenEstimator = None

def calibrate_model(model, X_val: pd.DataFrame, y_val: pd.Series) -> CalibratedClassifierCV:
    """Calibrates the model using Isotonic regression."""
    print("Calibrating model...")
    if FrozenEstimator is not None:
        calibrated = CalibratedClassifierCV(estimator=FrozenEstimator(model), method='isotonic')
    else:
        # Fallback for older sklearn
        calibrated = CalibratedClassifierCV(estimator=model, method='isotonic', cv='prefit')
    
    calibrated.fit(X_val, y_val)
    return calibrated

def compute_metrics(y_true: pd.Series, y_pred_proba: np.ndarray) -> dict:
    """Computes AUC-PR and KS statistic."""
    auc_pr = average_precision_score(y_true, y_pred_proba)
    
    preds_pos = y_pred_proba[y_true == 1]
    preds_neg = y_pred_proba[y_true == 0]
    
    if len(preds_pos) > 0 and len(preds_neg) > 0:
        ks_stat, _ = ks_2samp(preds_pos, preds_neg)
    else:
        ks_stat = 0.0
        
    return {
        "auc_pr": auc_pr,
        "ks_stat": ks_stat
    }

def compute_expected_cost(y_true: pd.Series, y_pred_proba: np.ndarray, cost_matrix: dict, threshold: float) -> float:
    """
    Computes expected cost given a threshold and cost matrix.
    Defaults cost matrix is defined as {fn_cost: X, fp_cost: Y}.
    True Positive: Default, predicted Default (Good, action taken) -> Cost 0
    True Negative: Paid, predicted Paid (Good, no action) -> Cost 0
    False Negative: Default, predicted Paid (Approved a defaulter) -> Cost FN
    False Positive: Paid, predicted Default (Rejected a good payer) -> Cost FP
    """
    preds = (y_pred_proba >= threshold).astype(int)
    
    fn = np.sum((y_true == 1) & (preds == 0))
    fp = np.sum((y_true == 0) & (preds == 1))
    
    total_cost = fn * cost_matrix['fn_cost'] + fp * cost_matrix['fp_cost']
    return total_cost / len(y_true)  # Average expected cost per applicant

def optimize_threshold(y_true: pd.Series, y_pred_proba: np.ndarray, cost_matrix: dict) -> tuple:
    """Finds the optimal probability threshold that minimizes expected cost."""
    thresholds = np.linspace(0.01, 0.99, 99)
    costs = [compute_expected_cost(y_true, y_pred_proba, cost_matrix, t) for t in thresholds]
    
    min_cost_idx = np.argmin(costs)
    optimal_threshold = thresholds[min_cost_idx]
    min_cost = costs[min_cost_idx]
    
    return optimal_threshold, min_cost

def plot_calibration_curve_to_file(y_true: pd.Series, y_pred_proba: np.ndarray, filepath: str):
    """Plots and saves the calibration curve."""
    prob_true, prob_pred = calibration_curve(y_true, y_pred_proba, n_bins=10)
    
    plt.figure(figsize=(8, 8))
    plt.plot(prob_pred, prob_true, marker='o', label="Model")
    plt.plot([0, 1], [0, 1], linestyle='--', color='gray', label="Perfectly calibrated")
    plt.xlabel("Mean predicted probability")
    plt.ylabel("Fraction of positives")
    plt.title("Calibration Curve")
    plt.legend()
    plt.grid(True)
    plt.savefig(filepath)
    plt.close()
