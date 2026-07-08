"""
Build the modeling dataset on the common grid:

  * present & future bioclim predictor stacks (standardized w/ present stats)
  * human modification H(x)
  * per-species spatially-thinned presence cells
  * target-group background (pooled multi-species observation effort)

Saves a single compressed npz used by every downstream stage.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
import config as C
import io_utils as IO

RNG = np.random.default_rng(C.RANDOM_SEED)


def lonlat_to_rc(lon, lat):
    """Map coordinates to grid row/col indices."""
    col = ((lon - C.LON_MIN) / C.GRID_RES).astype(int)
    row = ((C.LAT_MAX - lat) / C.GRID_RES).astype(int)
    return row, col


def main():
    print("[covariates] reading present climate ...")
    present = IO.read_worldclim_present(C.PREDICTORS)
    print("[covariates] reading future climate (ssp245) ...")
    future = IO.read_worldclim_future(C.PREDICTORS, scenario="ssp245")
    print("[covariates] reading future climate (ssp585) ...")
    future585 = IO.read_worldclim_future(C.PREDICTORS, scenario="ssp585")
    print("[covariates] reading human modification ...")
    H = IO.read_ghm()

    mask = IO.land_mask(present)          # valid land cells
    # require future validity too (both scenarios)
    for b in C.PREDICTORS:
        mask &= np.isfinite(future[b]) & np.isfinite(future585[b])
    ny, nx = mask.shape
    print(f"[covariates] grid {ny}x{nx}, land cells = {mask.sum()}")

    # ---- stack & standardize (present statistics applied to both epochs) ----
    P = np.stack([present[b] for b in C.PREDICTORS], axis=0).astype("float32")
    F = np.stack([future[b] for b in C.PREDICTORS], axis=0).astype("float32")
    F5 = np.stack([future585[b] for b in C.PREDICTORS], axis=0).astype("float32")
    mu = np.array([np.nanmean(P[i][mask]) for i in range(P.shape[0])])
    sd = np.array([np.nanstd(P[i][mask]) + 1e-9 for i in range(P.shape[0])])
    Pz = (P - mu[:, None, None]) / sd[:, None, None]
    Fz = (F - mu[:, None, None]) / sd[:, None, None]
    Fz585 = (F5 - mu[:, None, None]) / sd[:, None, None]

    # fill H nodata over land with domain median (rare gaps on coasts)
    Hf = H.copy()
    med = np.nanmedian(Hf[mask & np.isfinite(Hf)])
    Hf[~np.isfinite(Hf)] = med

    # ---- occurrences: spatial thinning to one presence per grid cell ----
    occ_all = pd.read_csv(C.DATA_RAW / "occ_ALL.csv")
    occ_all = occ_all[
        (occ_all.lon >= C.LON_MIN) & (occ_all.lon <= C.LON_MAX)
        & (occ_all.lat >= C.LAT_MIN) & (occ_all.lat <= C.LAT_MAX)
    ].copy()
    r, c = lonlat_to_rc(occ_all.lon.values, occ_all.lat.values)
    inb = (r >= 0) & (r < ny) & (c >= 0) & (c < nx)
    occ_all = occ_all[inb].copy()
    occ_all["row"] = r[inb]
    occ_all["col"] = c[inb]
    occ_all = occ_all[mask[occ_all.row.values, occ_all.col.values]]

    # target-group background: unique effort cells across ALL species
    tg_cells = np.unique(occ_all.row.values * nx + occ_all.col.values)
    print(f"[covariates] target-group effort cells = {len(tg_cells)}")

    presence = {}
    for sp in C.SPECIES_NAMES:
        s = occ_all[occ_all.species == sp]
        cells = np.unique(s.row.values * nx + s.col.values)
        presence[sp] = cells
        print(f"    {sp:22s}: {len(s):6d} records -> {len(cells):5d} thinned cells")

    # background sample: draw from target-group effort cells (bias correction),
    # plus a modest fraction of random land cells for domain coverage.
    land_flat = np.flatnonzero(mask.ravel())
    n_bg = min(20000, len(land_flat))
    n_tg = int(0.7 * n_bg)
    bg_tg = RNG.choice(tg_cells, size=min(n_tg, len(tg_cells)), replace=False)
    bg_rand = RNG.choice(land_flat, size=n_bg - len(bg_tg), replace=False)
    background = np.unique(np.concatenate([bg_tg, bg_rand]))
    print(f"[covariates] background cells = {len(background)}")

    np.savez_compressed(
        C.DATA_PROC / "dataset.npz",
        mask=mask,
        Pz=Pz, Fz=Fz, Fz585=Fz585, H=Hf.astype("float32"),
        mu=mu, sd=sd,
        predictors=np.array(C.PREDICTORS),
        lons=IO.GLONS, lats=IO.GLATS,
        background=background,
        tg_cells=tg_cells,
        nx=nx, ny=ny,
        **{f"pres__{sp}": presence[sp] for sp in C.SPECIES_NAMES},
    )
    print("[covariates] saved data/processed/dataset.npz")


if __name__ == "__main__":
    main()
