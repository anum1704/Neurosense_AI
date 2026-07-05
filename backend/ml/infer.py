"""
Inference on a new, unlabeled recording.

This module does NOT reimplement any ML math. It:
  1. Loads the exact fitted scaler / ensemble model / selected-feature-column
     list / Youden threshold produced by train.py.
  2. Slides the SAME window (ml.features.window_unlabeled) over the new signal.
  3. Runs the SAME extract() on every window.
  4. Subsets to the SAME selected_feature_columns, in the SAME order.
  5. Calls the SAME scaler.transform() and ensemble.predict_proba().

Aggregation rule (confirmed with user):
  - Every 5s window gets its own seizure probability from the ensemble.
  - The FINAL prediction is: average(all window probabilities) > saved_threshold.
  - Percentage of seizure windows and max probability are computed ONLY for
    display/explainability and never influence the prediction.
"""

import os
import json
import pickle

import numpy as np
import pandas as pd

from ml.config import (SCALER_PATH, MODEL_PATH, FEATURE_COLS_PATH,
                        THRESHOLD_PATH)
from ml.features import (load_mat_file, load_csv_file,
                          window_unlabeled, make_df_unlabeled,
                          make_df_unlabeled_parallel)


class SeizureInferenceEngine:
    def __init__(self, artifacts_dir="artifacts"):
        with open(os.path.join(artifacts_dir, "scaler.pkl"), "rb") as f:
            self.scaler = pickle.load(f)
        with open(os.path.join(artifacts_dir, "ensemble_model.pkl"), "rb") as f:
            self.model = pickle.load(f)
        with open(os.path.join(artifacts_dir, "selected_feature_columns.pkl"), "rb") as f:
            self.selected_columns = pickle.load(f)
        with open(os.path.join(artifacts_dir, "youden_threshold.json"), "r") as f:
            th_data = json.load(f)
        self.threshold = th_data["threshold"]
        self.training_metrics = th_data

    def _load_array(self, path):
        ext = os.path.splitext(path)[1].lower()
        if ext == ".mat":
            df = load_mat_file(path)
        elif ext == ".csv":
            df = load_csv_file(path)
        else:
            raise ValueError(f"Unsupported file type: {ext}. Use .mat or .csv")
        return df.values.astype(np.float32)

    def predict(self, path):
        arr = self._load_array(path)

        # Same sliding window as training, unlabeled.
        segs = window_unlabeled(arr)
        if len(segs) == 0:
            raise ValueError(
                "Recording is shorter than one window (5s @ 512Hz = 2560 samples); "
                "cannot run inference."
            )

        # Same feature extraction as training, run across CPU cores for speed
        # (identical values to the sequential version — see make_df_unlabeled_parallel).
        # Falls back to the original sequential path if multiprocessing isn't
        # available in the current environment (e.g. some restricted setups).
        try:
            feat_df = make_df_unlabeled_parallel(segs)
        except Exception:
            feat_df = make_df_unlabeled(segs)

        # Same feature subset, same order as training.
        feat_df = feat_df.reindex(columns=self.selected_columns)

        # --- Guard rail: catch channel-count / shape mismatches before they
        # silently corrupt predictions. Each channel contributes 20 features
        # (see extract()); the saved selected_columns indices only make sense
        # for the channel layout used during training. If the uploaded
        # recording has a different channel count, extract() produces a
        # shorter/longer feature vector, reindex() fills the missing columns
        # with NaN, and tree models (XGBoost/LightGBM in particular) route
        # NaN down a fixed default branch — which can saturate every
        # window's probability toward the same extreme value. Fail clearly
        # instead of returning a meaningless "all 1.0" result.
        if feat_df.isna().any().any():
            n_channels_uploaded = arr.shape[1] if arr.ndim > 1 else 1
            bad_cols = feat_df.columns[feat_df.isna().any()].tolist()
            raise ValueError(
                f"Feature mismatch: the uploaded recording has {n_channels_uploaded} "
                f"channel(s), which doesn't produce the same feature layout the model "
                f"was trained on (missing columns: {bad_cols}). Re-export the recording "
                "with the same channel count/order used for training, or retrain the "
                "model on data with this channel layout."
            )

        # Same scaler, same model.
        X_scaled = self.scaler.transform(feat_df)
        window_probs = self.model.predict_proba(X_scaled)[:, 1]

        # ---- Aggregation (per confirmed spec) ----
        total_windows = len(window_probs)
        avg_prob = float(np.mean(window_probs))
        max_prob = float(np.max(window_probs))
        seizure_windows = int(np.sum(window_probs > self.threshold))  # display only
        pct_seizure_windows = float(seizure_windows / total_windows * 100)  # display only

        # THE prediction — average probability vs. saved threshold. Nothing else.
        is_seizure = bool(avg_prob > self.threshold)

        # Confidence in the predicted class (standard definition: how far the
        # winning class's probability mass is from 0, i.e. distance from the
        # opposite class boundary).
        confidence = avg_prob if is_seizure else (1.0 - avg_prob)

        # Risk banding — explainability only, derived from avg_prob vs threshold,
        # does not affect is_seizure.
        risk_level = self._risk_level(avg_prob, self.threshold, is_seizure)

        return {
            "prediction": "SEIZURE" if is_seizure else "NON_SEIZURE",
            "total_windows": total_windows,
            "seizure_windows": seizure_windows,
            "seizure_windows_pct": round(pct_seizure_windows, 2),
            "avg_seizure_probability": round(avg_prob, 4),
            "max_seizure_probability": round(max_prob, 4),
            "confidence": round(confidence, 4),
            "risk_level": risk_level,
            "threshold_used": round(self.threshold, 4),
        }

    @staticmethod
    def _risk_level(avg_prob, threshold, is_seizure):
        """
        Explainability-only banding around the decision threshold.
        Does not feed back into `is_seizure`.
        """
        if not is_seizure:
            return "LOW" if avg_prob < threshold * 0.5 else "MODERATE"
        upper_band = threshold + (1.0 - threshold) * 0.5
        return "HIGH" if avg_prob < upper_band else "CRITICAL"
