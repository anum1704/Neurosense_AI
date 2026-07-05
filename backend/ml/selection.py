"""
Feature selection — copied verbatim from the notebook's Cell 4.
"""

import numpy as np
from sklearn.feature_selection import mutual_info_classif

from ml.config import N_FEAT, SEED


def select(X, y, k=N_FEAT):
    X = X.loc[:, X.var() > X.var().quantile(0.05)]
    mi = mutual_info_classif(X, y, random_state=SEED)
    sel = X.iloc[:, np.argsort(mi)[-k:]].copy()
    print(f"Features: kept {k} / {X.shape[1]}")
    return sel
