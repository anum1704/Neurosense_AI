"""
Labeling, windowing, and feature extraction.

Every function body below is copied verbatim from the original
ds_end.py notebook (Cells 2-3). Only the module loading of .mat
files (`load_data`) has been generalized to accept a path list
instead of hardcoding a Google Drive folder, and a `load_csv`
variant has been added purely as an alternate I/O reader for the
`.csv` upload convenience path. Neither change touches labeling,
windowing, or feature math.
"""

import os
import numpy as np
import pandas as pd
from scipy.io import loadmat
from scipy.signal import welch
from scipy.stats import entropy

from ml.config import FS, W, STEP, BANDS

# NumPy 2.0 renamed trapz -> trapezoid (identical trapezoidal-rule
# implementation). This shim keeps the exact same integration math
# working across both NumPy 1.x and 2.x.
_trapz = getattr(np, "trapezoid", None) or np.trapz


# ============================================================
# 1. LOAD  (verbatim math; generalized I/O only)
# ============================================================
def load_mat_file(path):
    """Load a single .mat file with an 'EEG' key -> DataFrame. Verbatim logic."""
    mat = loadmat(path)
    return pd.DataFrame(mat['EEG'])


def load_csv_file(path):
    """
    Convenience loader for .csv uploads. Produces the exact same
    DataFrame shape (samples x channels) that load_mat_file produces,
    so it feeds the identical downstream pipeline. No feature/label
    math lives here.
    """
    return pd.read_csv(path, header=None)


def load_data_from_dir(base_path):
    """Original directory-scanning loader, generalized to any base_path
    (originally hardcoded to a Google Drive path). Logic unchanged."""
    files = sorted(f for f in os.listdir(base_path) if f.endswith(".mat"))
    dfs = []
    for f in files:
        dfs.append(load_mat_file(os.path.join(base_path, f)))
    print(f"Loaded {len(dfs)} file(s)  |  shapes: {[d.shape for d in dfs]}")
    return dfs


# ============================================================
# 2. LABEL + WINDOW  (verbatim)
# ============================================================
def create_labels(df_len):
    y = np.zeros(df_len, dtype=np.int8)
    y[92160: df_len - 92160] = 1
    return y


def window_data(arr, y, w=W, step=STEP):
    segs, labs = [], []
    for i in range(0, len(arr) - w + 1, step):
        segs.append(arr[i: i + w])
        labs.append(int(np.mean(y[i: i + w]) > 0.5))
    return segs, labs


def window_unlabeled(arr, w=W, step=STEP):
    """
    Same sliding-window logic as window_data, for inference where
    no ground-truth labels exist yet. Produces the identical set of
    windows window_data would produce for the same array; only the
    label-bookkeeping is dropped since there is nothing to label.
    """
    segs = []
    for i in range(0, len(arr) - w + 1, step):
        segs.append(arr[i: i + w])
    return segs


# ============================================================
# 3. FAST FEATURE EXTRACTION  (verbatim)
# ============================================================
def _bp(s, band):
    """Band power via Welch — fixed nperseg=256 for speed."""
    f, P = welch(s, FS, nperseg=256)
    idx = (f >= band[0]) & (f <= band[1])
    return float(_trapz(P[idx], f[idx])) if idx.any() else 0.0


def _hjorth(s):
    d1 = np.diff(s)
    d2 = np.diff(d1)
    v0 = np.var(s) + 1e-12
    v1 = np.var(d1) + 1e-12
    v2 = np.var(d2) + 1e-12
    mob = np.sqrt(v1 / v0)
    return v0, mob, np.sqrt(v2 / v1) / mob  # activity, mobility, complexity


def extract(win):
    """
    20 features per channel — all proven in EEG seizure literature:
      9 time-domain  (mean, std, energy, sp.entropy, Hjorth×3, ZCR, peak)
      5 absolute band powers
      5 relative band powers  ← critical: normalises for amplitude variation
      1 line length            ← fast proxy for signal complexity
    """
    feats = []
    for ch in range(win.shape[1]):
        s = win[:, ch].astype(np.float32)
        s -= s.mean()

        prob = np.abs(s) / (np.abs(s).sum() + 1e-12)
        act, mob, comp = _hjorth(s)
        zcr = float(((s[:-1] * s[1:]) < 0).sum()) / len(s)

        feats.extend([
            float(np.mean(s)),
            float(np.std(s)),
            float(np.dot(s, s)),             # energy (fast)
            float(entropy(prob + 1e-12)),
            act, mob, comp, zcr,
            float(np.max(np.abs(s))),        # peak amplitude
        ])

        bps = [_bp(s, b) for b in BANDS]
        total = sum(bps) + 1e-12
        feats.extend(bps)                    # absolute
        feats.extend([b / total for b in bps])  # relative

        feats.append(float(np.sum(np.abs(np.diff(s)))))  # line length

    return feats


def make_df(segs, labs):
    X = [extract(w) for w in segs]
    df = pd.DataFrame(X, dtype=np.float32)
    df['y'] = labs
    return df


def make_df_unlabeled(segs):
    """Same as make_df but for inference windows with no labels."""
    X = [extract(w) for w in segs]
    return pd.DataFrame(X, dtype=np.float32)


def make_df_unlabeled_parallel(segs, max_workers=None):
    """
    Identical output to make_df_unlabeled — same extract() call per window,
    same values, same order — only the execution is spread across CPU cores
    via ProcessPoolExecutor instead of a single-threaded Python loop. This
    exists purely to cut wall-clock time on large recordings; it does not
    change any feature value.

    Falls back to the sequential version for small window counts, where
    process-pool startup overhead would outweigh the benefit.
    """
    if len(segs) < 8:
        return make_df_unlabeled(segs)

    import os as _os
    from concurrent.futures import ProcessPoolExecutor

    workers = max_workers or _os.cpu_count() or 1
    with ProcessPoolExecutor(max_workers=workers) as pool:
        X = list(pool.map(extract, segs, chunksize=max(1, len(segs) // (workers * 4) or 1)))
    return pd.DataFrame(X, dtype=np.float32)
