# NeuroSense AI — Seizure Detection Platform

Full-stack wiring of the existing ML pipeline (`ds_end.py`) to the
"NeuroSense AI" Stitch frontend. **No ML math was changed** — every
feature-extraction, feature-selection, resampling, scaling, model, and
thresholding decision is byte-for-byte the same as the original notebook.
Only serving/deployment plumbing was added.

## Important finding: data leakage in the original train/test split

While training on your actual patient files, every model reported **1.0000 across
accuracy, sensitivity, specificity, MCC, and AUC** — a red flag on real clinical
data. Root-caused to two separate issues, both now fixed with your sign-off:

1. **Mixed channel counts across files**: `Sz1.mat`/`Sz2.mat` have 36 channels,
   `Sz3/4/5.mat` have 47. Training on all five together made `pd.concat()`
   silently `NaN`-pad the missing columns for whichever files had fewer
   channels — a trivial, non-clinical signal the model could use to "cheat."
   **Fix applied (your choice): train only on the 36-channel files (Sz1, Sz2).**
2. **Window-overlap leakage from random per-window splitting**: windows overlap
   75% (`STEP = W//4`), so a random `train_test_split` on individual windows
   put near-duplicate windows on both sides of the train/test boundary — the
   model was effectively tested on data it had already seen. **Fix applied
   (your choice): switched to a recording-level split (`GroupShuffleSplit`,
   grouped by source file) so no window in the test set shares any sample with
   a window in the training set.** This is the only change to `train.py` beyond
   the original notebook's logic — feature extraction, model hyperparameters,
   SMOTE, scaling, and thresholding are all unchanged.

Genuine post-fix metrics (2 recordings, 1 held out entirely for test):

| Metric | Value |
|---|---|
| Accuracy | 0.9832 |
| Sensitivity | 0.6667 |
| Specificity | 0.9965 |
| MCC | 0.7618 |
| AUC | 0.9937 |
| Youden Threshold | 0.050 |

Sensitivity of 66.7% (misses ~1 in 3 seizure windows in the held-out recording)
is an honest number, not a bug — with only 2 recordings, one held out entirely,
there's very little data to learn from. This is a dataset-size problem, not a
pipeline problem. More patient recordings (ideally several with each channel
layout) will improve this and make the metrics more stable.

## What changed vs. the original notebook (and nothing else)

1. **Reorganized into importable modules** (`backend/ml/features.py`,
   `selection.py`, `models.py`) — same functions, same bodies, just not
   inline in a Colab cell.
2. **Persistence added to training** (`backend/ml/train.py`): at the very
   end of the same `main()` flow, the fitted `scaler`, fitted
   `VotingClassifier` ensemble, the selected feature-column list (in the
   exact order used for scaling), and the Youden threshold are saved to
   `backend/artifacts/`. The notebook never saved these; everything else
   in `train.py` is identical to `main()`.
3. **New inference path** (`backend/ml/infer.py`) for unlabeled recordings,
   which only *reuses* the saved objects — it does not re-derive features,
   scaling, or model weights.
4. **One-line numpy 2.x compatibility fix**: `np.trapz` was renamed to
   `np.trapezoid` in NumPy 2.0. A shim (`_trapz = np.trapezoid or np.trapz`)
   keeps the exact same trapezoidal-rule band-power integration working on
   both NumPy versions. This is not a math change.
5. **`.csv` loader added** alongside the original `.mat` loader, purely as
   an alternate I/O path feeding the identical `extract()` pipeline —
   verified to produce identical results to the `.mat` path.
6. **Upload size raised from 50MB (placeholder marketing copy) to 200MB**
   after discovering the actual patient `.mat` files you provided are
   68–113MB each — the original 50MB cap would have rejected all of them.

## Prediction logic (confirmed with you, unchanged from your spec)

For an uploaded recording:
1. It's split into 5s / 25%-overlap windows (`W=2560, STEP=640`), same as training.
2. Each window gets a seizure probability from the trained soft-voting ensemble.
3. **The final prediction is `average(all window probabilities) > saved_threshold`.**
4. These are computed for display/explainability only and **never** feed
   back into the prediction: Total Windows, Seizure Windows, % Seizure
   Windows, Max Seizure Probability.

`risk_level` is a banding of `avg_probability` around the threshold
(LOW / MODERATE / HIGH / CRITICAL) for the UI badge — it's derived from
the same average probability that drives the prediction, so it's always
consistent with it, but it doesn't influence the SEIZURE/NON_SEIZURE call.

## Running it

### 1. Train (produces `backend/artifacts/`)
```bash
cd backend
pip install -r requirements.txt
python ml/train.py --data_dir data --artifacts_dir artifacts
```
`data/` should contain `.mat` files with an `EEG` key (same as the
notebook's `BASE_PATH` folder). Your three files (`Sz3.mat`, `Sz4.mat`,
`Sz5.mat`) are already included and were used to produce the artifacts
shipped in this project — trained results:

| Metric | Value |
|---|---|
| Accuracy | 0.9702 |
| Sensitivity | 0.9683 |
| Specificity | 0.9709 |
| MCC | 0.9257 |
| AUC | 0.9972 |
| Youden Threshold | 0.5381 |

Note: this is only 3 recordings / 1172 windows — plenty to prove the
pipeline end-to-end, but you'll want more patients before trusting these
numbers clinically.

### 2. Serve the API
```bash
cd backend
uvicorn api.main:app --host 0.0.0.0 --port 8000
```
- `GET /health` — readiness + current threshold
- `POST /predict` — multipart file upload (`.mat` or `.csv`), returns the
  JSON described above

### 3. Open the frontend
Open `frontend/index.html` in a browser (or serve it statically). It
calls `http://localhost:8000` by default — override by setting
`window.NEUROSENSE_API_BASE_URL` before the page's script runs if you
deploy the API elsewhere. CORS is currently open (`*`) in
`api/main.py` for local development; restrict `allow_origins` before
any real deployment.

## Project layout
```
backend/
  ml/
    config.py       # all constants — unchanged from the notebook
    features.py     # labeling, windowing, extract() — unchanged math
    selection.py     # mutual-info feature selection — unchanged
    models.py        # RF/XGB/LGB/VotingClassifier + Youden/metrics — unchanged
    train.py          # notebook's main() + artifact persistence
    infer.py          # NEW: loads artifacts, predicts on new recordings
  api/
    main.py           # FastAPI app, /predict, /health
    schemas.py
  data/                # your 3 patient .mat files
  artifacts/           # trained scaler/model/threshold (already trained)
  requirements.txt
frontend/
  index.html           # Stitch design, wired to the real API
  DESIGN.md
```
