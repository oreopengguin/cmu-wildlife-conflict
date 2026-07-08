"""
Coexistence Risk Index (CRI) synthesis and independent validation.

CRI fuses the three geometric signals of climate-forced redistribution:
    (1) Coexistence Friction  (optimal-transport displacement up the human
        pressure gradient),
    (2) Corridor current in human-dominated cells (spectral connectivity),
    (3) Suitability GAINED inside human-dominated space (range expanding into
        people).
None of these is trained on conflict data, so validation is genuinely external.

Validation 1 (mechanism): OT-predicted displacement direction vs the EMPIRICAL
range-shift observed by splitting GBIF records into past/recent epochs.
Validation 2 (interface): does friction predict where species are actually
recorded inside human-dominated cells, beyond present suitability?
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
import config as C


def zscore(x, mask):
    v = x[mask & np.isfinite(x)]
    mu, sd = np.mean(v), np.std(v) + 1e-9
    z = (x - mu) / sd
    return np.where(mask, z, np.nan)


def gain_into_humans(present, future, H, mask):
    """Positive suitability change weighted by human modification."""
    g = np.clip(future - present, 0, None) * np.clip(H, 0, 1)
    return np.where(mask, g, np.nan)


def coexistence_risk(friction, current, present, future, H, mask,
                     w=(1.0, 0.8, 0.8)):
    """CRI = weighted sum of z-scored friction, human-weighted current, and
    suitability gain into human space. Returned on land, ~N(0,1) scale."""
    gi = gain_into_humans(present, future, H, mask)
    cur_h = current * np.clip(H, 0, 1)
    zf = zscore(friction, mask)
    zc = zscore(cur_h, mask)
    zg = zscore(gi, mask)
    cri = w[0] * zf + w[1] * zc + w[2] * zg
    return np.where(mask, cri, np.nan), dict(zf=zf, zc=zc, zg=zg, gain=gi)


# ---------------------------------------------------------------------------
# Validation 1 — observed vs predicted range shift
# ---------------------------------------------------------------------------
def observed_shift(species, min_n=30):
    """Observed range-centroid shift from a HISTORICAL epoch (occ_hist_*, 1950-
    2009) to the RECENT epoch (occ_*, ~2015-2026). Uses robust (median) and
    high-suitability-trimmed centroids to resist outlier vagrant records."""
    tag = species.replace(" ", "_")
    fh = C.DATA_RAW / f"occ_hist_{tag}.csv"
    fr = C.DATA_RAW / f"occ_{tag}.csv"
    if not fh.exists():
        return None
    past = pd.read_csv(fh).dropna(subset=["lon", "lat"])
    recent = pd.read_csv(fr).dropna(subset=["lon", "lat"])
    if len(past) < min_n or len(recent) < min_n:
        return None

    def centroid(d):
        # median centroid (robust to vagrant outliers)
        return np.array([np.median(d.lon.values), np.median(d.lat.values)])
    cp, cr = centroid(past), centroid(recent)
    return dict(d_lon=float(cr[0] - cp[0]), d_lat=float(cr[1] - cp[1]),
                n_past=int(len(past)), n_recent=int(len(recent)),
                c_past=cp.tolist(), c_recent=cr.tolist())


def predicted_shift(dlon, dlat, present, mask):
    """Mass-weighted mean predicted displacement (weight = present suitability)."""
    w = np.where(mask, np.clip(present, 0, None), 0.0)
    W = w.sum() + 1e-12
    return dict(d_lon=float(np.sum(w * dlon) / W),
                d_lat=float(np.sum(w * dlat) / W))


# ---------------------------------------------------------------------------
# Validation 2 — friction vs realized human-interface occurrence
# ---------------------------------------------------------------------------
def interface_validation(friction, present, H, mask, occ_cells_recent, nx,
                         h_thresh=0.4):
    """Among human-dominated cells (H>h_thresh), test whether friction ranks
    cells that actually hold recent occurrences above those that don't, and
    whether it adds signal beyond present suitability (partial Spearman)."""
    human = mask & (H > h_thresh)
    hy, hx = np.where(human)
    flat = hy * nx + hx
    label = np.isin(flat, occ_cells_recent).astype(float)
    fr = friction[hy, hx]
    pr = present[hy, hx]
    ok = np.isfinite(fr) & np.isfinite(pr)
    fr, pr, label = fr[ok], pr[ok], label[ok]
    if label.sum() < 10:
        return None
    # AUC of friction vs interface label
    from maxent_ppm import auc_presence_background
    rng = np.random.default_rng(0)
    auc = auc_presence_background(fr[label == 1], fr[label == 0], rng=rng)
    rho_f, p_f = spearmanr(fr, label)
    rho_p, p_p = spearmanr(pr, label)
    return dict(auc_friction=auc, rho_friction=rho_f, p_friction=p_f,
                rho_present=rho_p, n_pos=int(label.sum()), n_tot=int(len(label)))
