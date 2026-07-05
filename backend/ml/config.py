# ============================================================
# CONFIG — copied verbatim from the original notebook (ds_end.py)
# DO NOT CHANGE any of these values. Changing them changes the
# mathematical behavior of the pipeline.
# ============================================================

FS       = 512
W        = 2560          # 5 s window
STEP     = W // 4        # 25% overlap — key for capturing onset/offset
N_FEAT   = 50             # top MI features
N_TREES  = 120            # per forest/boosting model
SEED     = 42
BANDS    = [(0.5, 4), (4, 8), (8, 13), (13, 30), (30, 60)]

# Where trained artifacts are written/read from
ARTIFACTS_DIR = "artifacts"
SCALER_PATH        = f"{ARTIFACTS_DIR}/scaler.pkl"
MODEL_PATH         = f"{ARTIFACTS_DIR}/ensemble_model.pkl"
FEATURE_COLS_PATH  = f"{ARTIFACTS_DIR}/selected_feature_columns.pkl"
THRESHOLD_PATH     = f"{ARTIFACTS_DIR}/youden_threshold.json"
FEATURE_NAMES_PATH = f"{ARTIFACTS_DIR}/all_feature_names.pkl"
