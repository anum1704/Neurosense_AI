"""
Model constructors, thresholding, and metrics — copied verbatim
from the notebook's Cells 5-6.
"""

import numpy as np
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.metrics import (accuracy_score, confusion_matrix,
                              matthews_corrcoef, roc_curve, auc)
import xgboost as xgb
import lightgbm as lgb

from ml.config import N_TREES, SEED


# ============================================================
# 5. THRESHOLD + METRICS  (verbatim)
# ============================================================
def youden_thresh(y_true, probs):
    if len(np.unique(probs)) < 2:
        return 0.5, [0, 1], [0, 1], 0.5
    fpr, tpr, thr = roc_curve(y_true, probs)
    j = tpr - fpr
    best = np.argmax(j)
    return float(np.clip(thr[best], 0.05, 0.95)), fpr, tpr, float(auc(fpr, tpr))


def metrics(y_true, y_pred):
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    return (accuracy_score(y_true, y_pred),
            tp / (tp + fn + 1e-12),   # sensitivity
            tn / (tn + fp + 1e-12),   # specificity
            matthews_corrcoef(y_true, y_pred))


def show(name, acc, sen, spe, mcc, aucv):
    ok = lambda v, t: "OK" if v >= t else "X"
    print(f"\n{'-'*46}")
    print(f"  {name}")
    print(f"  Accuracy    {acc:.4f}  {ok(acc,0.95)}  (target >=0.95)")
    print(f"  Sensitivity {sen:.4f}  {ok(sen,0.90)}  (target >=0.90)")
    print(f"  Specificity {spe:.4f}  {ok(spe,0.90)}  (target >=0.90)")
    print(f"  MCC         {mcc:.4f}  {ok(mcc,0.90)}  (target >=0.90)")
    print(f"  AUC         {aucv:.4f}  {ok(aucv,0.90)}  (target >=0.90)")


# ============================================================
# 6. MODELS  (verbatim — 3 fast complementary models)
# ============================================================
def make_rf():
    return RandomForestClassifier(
        n_estimators=N_TREES,
        max_depth=None,
        min_samples_leaf=2,
        max_features='sqrt',
        class_weight='balanced',
        n_jobs=-1,
        random_state=SEED
    )


def make_xgb():
    return xgb.XGBClassifier(
        n_estimators=N_TREES,
        max_depth=5,
        learning_rate=0.1,
        subsample=0.85,
        colsample_bytree=0.85,
        use_label_encoder=False,
        eval_metric='logloss',
        n_jobs=-1,
        random_state=SEED
    )


def make_lgb():
    return lgb.LGBMClassifier(
        n_estimators=N_TREES,
        learning_rate=0.1,
        max_depth=6,
        num_leaves=31,
        class_weight='balanced',
        n_jobs=-1,
        random_state=SEED,
        verbose=-1
    )


def make_voting_ensemble():
    """
    Soft voting averages predicted probabilities.
    RF + XGB + LGB have very different decision boundaries
    (bagging vs boosting vs gradient boosting) so their
    errors are largely independent — averaging cancels them.
    """
    return VotingClassifier(
        estimators=[('rf', make_rf()),
                    ('xgb', make_xgb()),
                    ('lgb', make_lgb())],
        voting='soft',
        n_jobs=-1
    )
