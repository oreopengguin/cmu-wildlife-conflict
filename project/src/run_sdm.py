"""
Fit the from-scratch MaxEnt/PPP model for every species, evaluate with spatial
block cross-validation, and project present + future suitability surfaces.

Outputs results/sdm.npz with, per species:
    suit_present, suit_future  (grid arrays over land)
    cv metrics (AUC, Boyce, TSS) mean/sd across spatial folds
"""
from __future__ import annotations
import numpy as np
import config as C
from maxent_ppm import (FeatureMaker, MaxentPPM,
                        auc_presence_background, boyce_index, tss_max)

RNG = np.random.default_rng(C.RANDOM_SEED)


def load():
    d = np.load(C.DATA_PROC / "dataset.npz", allow_pickle=True)
    return d


def cell_covariates(Pz, cells, nx):
    """Extract predictor vectors (n_pred,) for flat cell indices."""
    r = cells // nx
    c = cells % nx
    return Pz[:, r, c].T          # (ncells, n_pred)


def spatial_blocks(cells, nx, ny, block=6, k=4, rng=None):
    """Assign flat cells to k spatial folds by coarse block checkerboard."""
    rng = rng or np.random.default_rng(0)
    r = cells // nx
    c = cells % nx
    bid = (r // block) * (nx // block + 1) + (c // block)
    ub = np.unique(bid)
    fold_of_block = {b: rng.integers(0, k) for b in ub}
    return np.array([fold_of_block[b] for b in bid])


def main():
    d = load()
    Pz, Fz, H = d["Pz"], d["Fz"], d["H"]
    Fz585 = d["Fz585"]
    mask = d["mask"]; nx = int(d["nx"]); ny = int(d["ny"])
    background = d["background"]
    n_pred = Pz.shape[0]

    land_cells = np.flatnonzero(mask.ravel())
    bg_cov = cell_covariates(Pz, background, nx)

    fmaker = FeatureMaker(n_pred=n_pred, knots=4, use_products=True)
    # fit feature ranges on background (representative of domain)
    fmaker.fit(bg_cov)
    Mbg = fmaker.transform(bg_cov)

    # Berman-Turner weights: background carries cell area (equal), presence tiny
    area = 1.0
    results = {}
    metrics = {}
    for sp in C.SPECIES_NAMES:
        pres_cells = d[f"pres__{sp}"]
        if len(pres_cells) < 20:
            print(f"[sdm] skip {sp} (only {len(pres_cells)} cells)")
            continue
        pres_cov = cell_covariates(Pz, pres_cells, nx)
        Mp = fmaker.transform(pres_cov)

        # ---------- spatial block CV ----------
        folds_p = spatial_blocks(pres_cells, nx, ny, block=6, k=4, rng=RNG)
        aucs, boys, tsss = [], [], []
        for f in range(4):
            tr = folds_p != f
            te = folds_p == f
            if te.sum() < 5 or tr.sum() < 20:
                continue
            model = MaxentPPM(l1=1e-3, l2=1e-3, max_iter=500)
            M = np.vstack([Mp[tr], Mbg])
            y = np.concatenate([np.full(tr.sum(), 1.0), np.zeros(len(Mbg))])
            w = np.concatenate([np.full(tr.sum(), 1e-6), np.full(len(Mbg), area)])
            # Berman-Turner response = y / w
            ybt = y / w
            model.fit(M, ybt, w)
            sp_te = model.suitability(Mp[te])
            sp_bg = model.suitability(Mbg)
            aucs.append(auc_presence_background(sp_te, sp_bg, rng=RNG))
            boys.append(boyce_index(sp_te, sp_bg))
            tsss.append(tss_max(sp_te, sp_bg))
        metrics[sp] = dict(
            auc=(np.nanmean(aucs), np.nanstd(aucs)),
            boyce=(np.nanmean(boys), np.nanstd(boys)),
            tss=(np.nanmean(tsss), np.nanstd(tsss)),
            n_cells=len(pres_cells),
        )
        print(f"[sdm] {sp:22s} AUC={np.nanmean(aucs):.3f}±{np.nanstd(aucs):.3f} "
              f"Boyce={np.nanmean(boys):.3f} TSS={np.nanmean(tsss):.3f} "
              f"(n={len(pres_cells)})")

        # ---------- full fit + project present & future over all land ----------
        model = MaxentPPM(l1=1e-3, l2=1e-3, max_iter=800)
        M = np.vstack([Mp, Mbg])
        y = np.concatenate([np.full(len(Mp), 1.0), np.zeros(len(Mbg))])
        w = np.concatenate([np.full(len(Mp), 1e-6), np.full(len(Mbg), area)])
        model.fit(M, y / w, w)

        present_cov = cell_covariates(Pz, land_cells, nx)
        future_cov = cell_covariates(Fz, land_cells, nx)
        future5_cov = cell_covariates(Fz585, land_cells, nx)
        Mpr = fmaker.transform(present_cov, clamp=True)
        Mfu = fmaker.transform(future_cov, clamp=True)
        Mfu5 = fmaker.transform(future5_cov, clamp=True)
        suit_p = model.suitability(Mpr)
        suit_f = model.suitability(Mfu)
        suit_f5 = model.suitability(Mfu5)

        gp = np.full(ny * nx, np.nan); gp[land_cells] = suit_p
        gf = np.full(ny * nx, np.nan); gf[land_cells] = suit_f
        gf5 = np.full(ny * nx, np.nan); gf5[land_cells] = suit_f5
        results[f"present__{sp}"] = gp.reshape(ny, nx).astype("float32")
        results[f"future__{sp}"] = gf.reshape(ny, nx).astype("float32")
        results[f"future585__{sp}"] = gf5.reshape(ny, nx).astype("float32")
        results[f"nnz__{sp}"] = model.nnz_

    # save
    np.savez_compressed(
        C.RESULTS / "sdm.npz",
        land_cells=land_cells, nx=nx, ny=ny,
        mask=mask, H=H,
        lons=d["lons"], lats=d["lats"],
        **results,
    )
    import json
    with open(C.RESULTS / "sdm_metrics.json", "w") as fh:
        json.dump({k: {kk: (list(vv) if isinstance(vv, tuple) else vv)
                       for kk, vv in v.items()} for k, v in metrics.items()},
                  fh, indent=2)
    print("[sdm] saved results/sdm.npz and sdm_metrics.json")


if __name__ == "__main__":
    main()
