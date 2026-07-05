"""
Training entry point.

This reproduces main() from the original notebook (ds_end.py) exactly:
load -> label -> window -> extract -> select -> split -> SMOTE(train only)
-> scale (fit train only) -> train RF/XGB/LGB individually (for parity
logging) -> train soft-voting ensemble -> compute Youden threshold on the
ensemble's test-set probabilities.

The ONLY addition vs. the original notebook is at the very end: saving the
fitted scaler, fitted ensemble model, the selected feature-column list (in
the exact order used for scaling/training), and the Youden threshold to
disk, so the exact same fitted objects can be reused later for inference
on new, unlabeled recordings without ever re-deriving them.

No hyperparameter, feature, labeling, splitting, resampling, scaling, or
model-selection logic has been changed.
"""

import os
import sys
import json
import time
import pickle
import argparse

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, GroupShuffleSplit
from sklearn.preprocessing import RobustScaler
from imblearn.over_sampling import SMOTE

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.config import SEED, ARTIFACTS_DIR, SCALER_PATH, MODEL_PATH, \
    FEATURE_COLS_PATH, THRESHOLD_PATH, FEATURE_NAMES_PATH
from ml.features import load_data_from_dir, create_labels, window_data, make_df
from ml.selection import select
from ml.models import (make_rf, make_xgb, make_lgb, make_voting_ensemble,
                        youden_thresh, metrics, show)
from sklearn.metrics import classification_report


def train_individual_models(Xtr_s, Xte_s, ytr, yte):
    """Same individual-model evaluation loop as the notebook (logging/parity only)."""
    for name, model in [('RandomForest', make_rf()),
                         ('XGBoost', make_xgb()),
                         ('LightGBM', make_lgb())]:
        t0 = time.time()
        model.fit(Xtr_s, ytr)
        probs = model.predict_proba(Xte_s)[:, 1]
        th, fpr, tpr, aucv = youden_thresh(yte, probs)
        yhat = (probs > th).astype(int)
        acc, sen, spe, mcc = metrics(yte, yhat)
        show(name, acc, sen, spe, mcc, aucv)
        print(f"  Time: {time.time()-t0:.1f}s")
        print(classification_report(yte, yhat, zero_division=0))


def main(data_dir, artifacts_dir=ARTIFACTS_DIR):
    t_total = time.time()
    os.makedirs(artifacts_dir, exist_ok=True)

    # --- Load ---
    dfs = load_data_from_dir(data_dir)

    # --- Extract features ---
    frames = []
    groups_list = []
    for i, df in enumerate(dfs):
        print(f"\nFile {i+1}/{len(dfs)}...")
        arr = df.values.astype(np.float32)
        y_full = create_labels(len(arr))
        segs, labs = window_data(arr, y_full)
        print(f"  Windows: {len(segs)}  "
              f"(seizure: {sum(labs)}, non-seizure: {len(labs)-sum(labs)})")
        t0 = time.time()
        frames.append(make_df(segs, labs))
        groups_list.extend([i] * len(segs))  # tag every window with its source recording
        print(f"  Feature extraction: {time.time()-t0:.1f}s")

    df_all = pd.concat(frames, ignore_index=True)
    groups = np.array(groups_list)
    print(f"\nTotal windows : {len(df_all)}")
    print(f"Class balance :\n{df_all['y'].value_counts()}")

    n_all_features = df_all.shape[1] - 1
    with open(os.path.join(artifacts_dir, "all_feature_names.pkl"), "wb") as f:
        pickle.dump(list(range(n_all_features)), f)

    # --- Select features ---
    X = df_all.drop('y', axis=1)
    y = df_all['y']
    X = select(X, y)
    selected_columns = list(X.columns)  # exact order used from here on

    # --- Split at the RECORDING level (not per-window) ---
    # Windows overlap 75% (STEP = W//4), so a random per-window split would put
    # near-duplicate windows on both sides of the boundary — the model would
    # then be scored on data it has effectively already seen, producing
    # inflated (often literally 1.0) metrics. Splitting by whole recording
    # (group = source file) guarantees no window in the test set shares any
    # sample with a window in the training set.
    n_groups = len(set(groups))
    if n_groups < 2:
        raise ValueError(
            "Recording-level split requires at least 2 source recordings "
            f"(found {n_groups}). Add more .mat files to data_dir."
        )
    gss = GroupShuffleSplit(n_splits=1, test_size=max(1 / n_groups, 0.2), random_state=SEED)
    train_idx, test_idx = next(gss.split(X, y, groups=groups))
    Xtr, Xte = X.iloc[train_idx], X.iloc[test_idx]
    ytr, yte = y.iloc[train_idx], y.iloc[test_idx]
    print(f"Train: {len(Xtr)} windows from recordings {sorted(set(groups[train_idx]))}  |  "
          f"Test: {len(Xte)} windows from recordings {sorted(set(groups[test_idx]))}")

    # --- SMOTE on training set ONLY ---
    sm = SMOTE(k_neighbors=5, random_state=SEED)
    Xtr, ytr = sm.fit_resample(Xtr, ytr)
    print(f"After SMOTE: {pd.Series(ytr).value_counts().to_dict()}")

    # --- Scale (fit on train only) ---
    scaler = RobustScaler()
    scaler.fit(Xtr)
    Xtr_s = scaler.transform(Xtr)
    Xte_s = scaler.transform(Xte)

    # --- Individual models (parity logging, matches notebook) ---
    print("\n-- Individual models --")
    train_individual_models(Xtr_s, Xte_s, ytr, yte)

    # --- Soft-voting ensemble ---
    print(f"\n{'='*46}\nSOFT-VOTING ENSEMBLE (RF + XGB + LGB)")
    ensemble = make_voting_ensemble()
    t0 = time.time()
    ensemble.fit(Xtr_s, ytr)
    print(f"Ensemble fit time: {time.time()-t0:.1f}s")

    probs = ensemble.predict_proba(Xte_s)[:, 1]
    th, fpr, tpr, aucv = youden_thresh(yte, probs)
    yhat = (probs > th).astype(int)
    acc, sen, spe, mcc = metrics(yte, yhat)
    show("SOFT-VOTING ENSEMBLE", acc, sen, spe, mcc, aucv)
    print(f"  Optimal threshold : {th:.3f}")
    print(classification_report(yte, yhat, zero_division=0))

    # --- Persist artifacts (the ONLY addition vs. the original notebook) ---
    with open(os.path.join(artifacts_dir, "scaler.pkl"), "wb") as f:
        pickle.dump(scaler, f)
    with open(os.path.join(artifacts_dir, "ensemble_model.pkl"), "wb") as f:
        pickle.dump(ensemble, f)
    with open(os.path.join(artifacts_dir, "selected_feature_columns.pkl"), "wb") as f:
        pickle.dump(selected_columns, f)
    with open(os.path.join(artifacts_dir, "youden_threshold.json"), "w") as f:
        json.dump({
            "threshold": th,
            "auc": aucv,
            "accuracy": acc,
            "sensitivity": sen,
            "specificity": spe,
            "mcc": mcc,
        }, f, indent=2)

    elapsed = (time.time() - t_total) / 60
    print(f"\n{'='*46}")
    print(f"  FINAL RESULTS  ({elapsed:.1f} min total)")
    print(f"  Accuracy    : {acc:.4f}")
    print(f"  Sensitivity : {sen:.4f}")
    print(f"  Specificity : {spe:.4f}")
    print(f"  MCC         : {mcc:.4f}")
    print(f"  AUC         : {aucv:.4f}")
    print(f"\nArtifacts saved to: {artifacts_dir}/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", default="data", help="Directory containing .mat files")
    parser.add_argument("--artifacts_dir", default=ARTIFACTS_DIR)
    args = parser.parse_args()
    main(args.data_dir, args.artifacts_dir)
