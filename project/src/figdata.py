"""Loader utilities shared by all figure scripts."""
from __future__ import annotations
import json
import numpy as np
import pandas as pd
import config as C


def load_analysis():
    return np.load(C.RESULTS / "analysis.npz", allow_pickle=True)


def load_summary():
    with open(C.RESULTS / "summary.json") as fh:
        return json.load(fh)


def load_metrics():
    with open(C.RESULTS / "sdm_metrics.json") as fh:
        return json.load(fh)


def species_present(A):
    return [sp for sp in C.SPECIES_NAMES if f"present__{sp}" in A.files]


def load_occ(sp):
    return pd.read_csv(C.DATA_RAW / f"occ_{sp.replace(' ', '_')}.csv").dropna(
        subset=["lon", "lat"])


def load_all_occ():
    return pd.read_csv(C.DATA_RAW / "occ_ALL.csv").dropna(subset=["lon", "lat"])
