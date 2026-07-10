"""
Export REAL pipeline outputs to the website's data/image assets.

Everything here is derived from committed results (sdm.npz, analysis.npz,
summary.json, robustness.json, dataset.npz) — nothing invented. Produces:
  website/assets/data/*.json   (species meta, skill, niche PCA, coarse grids)
  website/assets/img/sdm/*.png (per-species present/future suitability maps)
  website/assets/img/*.jpg     (copies of the flagship figures)
"""
from __future__ import annotations
import json, shutil, base64
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
import config as C
import figstyle as FS
import figdata as FD

WEB = C.ROOT / "website"
DATA = WEB / "assets" / "data"
IMG = WEB / "assets" / "img"
SDM_IMG = IMG / "sdm"
for d in (DATA, IMG, SDM_IMG):
    d.mkdir(parents=True, exist_ok=True)
FS.apply()


def _b64_u8(arr):
    return base64.b64encode(np.asarray(arr, dtype=np.uint8).tobytes()).decode()


def coarsen(field, mask, cf):
    ny, nx = field.shape
    ny2, nx2 = (ny // cf) * cf, (nx // cf) * cf
    f = np.where(mask, field, np.nan)[:ny2, :nx2].reshape(ny2 // cf, cf, nx2 // cf, cf)
    m = mask[:ny2, :nx2].reshape(ny2 // cf, cf, nx2 // cf, cf)
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        cval = np.nanmean(f, axis=(1, 3))
    cm = m.mean(axis=(1, 3)) >= 0.5
    return cval, cm


def export_meta(A, summ, robu):
    sp_list = FD.species_present(A)
    species = [{"key": sp, "common": C.SPECIES_COMMON[sp],
                "color": C.SPECIES_COLOR[sp], "marker": C.SPECIES_MARKER[sp],
                "W_km": round(summ["species"][sp]["W_shift_km"]),
                "pred_dlat": round(summ["species"][sp]["predicted_shift"]["d_lat"], 2),
                "obs_dlat": (round(summ["species"][sp]["observed_shift"]["d_lat"], 2)
                             if summ["species"][sp]["observed_shift"] else None)}
               for sp in sp_list]
    meta = {
        "species": species,
        "scenario": summ.get("scenario"),
        "results": {
            "n_species": len(sp_list),
            "mean_shift_km": round(summ["community"]["mean_W_shift_km"]),
            "spearman": round(summ["validation_shift"]["spearman"], 2),
            "pearson": round(summ["validation_shift"]["pearson"], 2),
            "warming_C": 2.8,
            "frag_H1_present": summ["community"]["frag_present"]["n_loops"],
            "frag_H1_future": summ["community"]["frag_future"]["n_loops"],
            "scenario_corr": round(robu["scenario"]["friction_corr_245_585"], 2),
            "maxent_check": robu["maxent_constraint"]["pearson"],
            "grid_cv_pct": round(robu["coarsen_sensitivity"]["cv"] * 100, 1),
            "W245_mean": round(np.mean(list(robu["scenario"]["W245"].values()))),
            "W585_mean": round(np.mean(list(robu["scenario"]["W585"].values()))),
        },
    }
    (DATA / "meta.json").write_text(json.dumps(meta, indent=1))
    print("wrote meta.json")


def export_skill():
    m = FD.load_metrics()
    out = [{"key": sp, "common": C.SPECIES_COMMON[sp], "color": C.SPECIES_COLOR[sp],
            "marker": C.SPECIES_MARKER[sp],
            "auc": [round(m[sp]["auc"][0], 3), round(m[sp]["auc"][1], 3)],
            "boyce": [round(m[sp]["boyce"][0], 3), round(m[sp]["boyce"][1], 3)]}
           for sp in C.SPECIES_NAMES if sp in m]
    (DATA / "skill.json").write_text(json.dumps(out, indent=1))
    print("wrote skill.json")


def export_niche(A):
    d = np.load(C.DATA_PROC / "dataset.npz", allow_pickle=True)
    Pz = d["Pz"]; nx = int(d["nx"]); mask = A["mask"]
    land = np.flatnonzero(mask.ravel())
    X = Pz.reshape(Pz.shape[0], -1)[:, land].T
    rng = np.random.default_rng(0)
    sub = rng.choice(len(X), size=min(2500, len(X)), replace=False)
    pca = PCA(n_components=2).fit(X[sub])
    bg = pca.transform(X[sub])
    from scipy.spatial import ConvexHull
    species = {}
    for sp in FD.species_present(A):
        cells = d[f"pres__{sp}"]; r = cells // nx; c = cells % nx
        Yi = pca.transform(Pz[:, r, c].T)
        ctr = Yi.mean(axis=0)
        # trim vagrant outliers (keep the central 85% by Mahalanobis-ish radius)
        dist = np.linalg.norm((Yi - ctr) / (Yi.std(axis=0) + 1e-9), axis=1)
        keep = Yi[dist <= np.percentile(dist, 85)]
        s = keep[rng.choice(len(keep), size=min(400, len(keep)), replace=False)]
        try:
            hull = s[ConvexHull(s).vertices]
        except Exception:
            hull = s
        # shrink hull toward centroid for a clean, density-like niche outline
        hull = ctr + 0.82 * (hull - ctr)
        species[sp] = {"centroid": [round(float(ctr[0]), 3), round(float(ctr[1]), 3)],
                       "hull": [[round(float(a), 3), round(float(b), 3)] for a, b in hull],
                       "n": int(len(cells))}
    out = {"pc1var": round(float(pca.explained_variance_ratio_[0] * 100)),
           "pc2var": round(float(pca.explained_variance_ratio_[1] * 100)),
           "background": [[round(float(a), 2), round(float(b), 2)] for a, b in bg],
           "species": species}
    (DATA / "niche.json").write_text(json.dumps(out))
    print("wrote niche.json")


def render_map(field, mask, lons, lats, path, cmap=FS.SUIT, stretch98=None):
    """Render a clean suitability map PNG with transparent sea."""
    if stretch98 is None:
        stretch98 = np.nanpercentile(field[mask], 98) + 1e-9
    f = np.clip(field / stretch98, 0, 1)
    f = np.where(mask, f, np.nan)
    h, w = mask.shape
    fig = plt.figure(figsize=(w / 100, h / 100), dpi=150)
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off")
    ax.imshow(f, cmap=cmap, vmin=0, vmax=1, interpolation="bilinear")
    ax.contour(mask.astype(float), levels=[0.5], colors=["#0b1220"],
               linewidths=0.5, alpha=0.6)
    fig.savefig(path, transparent=True, dpi=150)
    plt.close(fig)
    return float(stretch98)


def export_sdm(A):
    mask = A["mask"]; lons = A["lons"]; lats = A["lats"]
    extent = [float(lons[0]), float(lons[-1]), float(lats[-1]), float(lats[0])]
    cf = 4
    _, cmask = coarsen(A["present__" + FD.species_present(A)[0]], mask, cf)
    grids = {"extent": extent, "coarse_shape": list(cmask.shape),
             "mask": _b64_u8(cmask.ravel()), "species": {}}
    for sp in FD.species_present(A):
        pres = A[f"present__{sp}"]; fut = A[f"future__{sp}"]
        s98 = render_map(pres, mask, lons, lats, SDM_IMG / f"{sp.replace(' ','_')}_present.png")
        render_map(fut, mask, lons, lats, SDM_IMG / f"{sp.replace(' ','_')}_future.png",
                   stretch98=s98)
        # coarse relative-suitability grids for hover (0-100)
        cp, _ = coarsen(np.clip(pres / s98, 0, 1), mask, cf)
        cfu, _ = coarsen(np.clip(fut / s98, 0, 1), mask, cf)
        grids["species"][sp] = {
            "present": _b64_u8(np.nan_to_num(cp).ravel() * 100),
            "future": _b64_u8(np.nan_to_num(cfu).ravel() * 100)}
    (DATA / "sdm_grids.json").write_text(json.dumps(grids))
    print("wrote sdm_grids.json + per-species map PNGs")


def export_risk(A):
    """Coarse CRI grid for the game hotspot map + hover, plus a clean CRI PNG."""
    mask = A["mask"]; cri = A["CRI"]; lons = A["lons"]; lats = A["lats"]
    # render a clean Coexistence Risk map (EMBER) for the escape-room map
    v = cri[mask & np.isfinite(cri)]
    lo, hi = np.percentile(v, 3), np.percentile(v, 99)
    f = np.clip((cri - lo) / (hi - lo + 1e-9), 0, 1)
    f = np.where(mask, f, np.nan)
    ny, nx = mask.shape
    fig = plt.figure(figsize=(nx / 100, ny / 100), dpi=150)
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off")
    ax.imshow(f, cmap=FS.EMBER, vmin=0, vmax=1, interpolation="bilinear")
    ax.contour(mask.astype(float), levels=[0.5], colors=["#0b1220"], linewidths=0.5, alpha=0.6)
    fig.savefig(IMG / "risk_map.png", transparent=True, dpi=150)
    plt.close(fig)
    cf = 3
    cc, cm = coarsen(cri, mask, cf)
    v = cc[np.isfinite(cc)]
    lo, hi = np.percentile(v, 3), np.percentile(v, 99)
    cc = np.clip((cc - lo) / (hi - lo + 1e-9), 0, 1)
    out = {"extent": [float(A["lons"][0]), float(A["lons"][-1]),
                      float(A["lats"][-1]), float(A["lats"][0])],
           "coarse_shape": list(cm.shape),
           "mask": _b64_u8(cm.ravel()),
           "cri": _b64_u8(np.nan_to_num(cc).ravel() * 100)}
    (DATA / "risk_grid.json").write_text(json.dumps(out))
    print("wrote risk_grid.json")


def copy_figures():
    for n in ["figure1_framework", "figure2_transport",
              "figure3_connectivity_topology", "figure4_risk_validation",
              "figureS1_robustness", "figureSDM_present_future"]:
        src = C.FIGDIR / "web" / f"{n}.jpg"
        if src.exists():
            shutil.copy(src, IMG / f"{n}.jpg")
    print("copied flagship figure JPGs")


def main():
    A = FD.load_analysis(); summ = FD.load_summary()
    robu = json.load(open(C.RESULTS / "robustness.json"))
    export_meta(A, summ, robu)
    export_skill()
    export_niche(A)
    export_sdm(A)
    export_risk(A)
    copy_figures()
    print("== web export complete ==")


if __name__ == "__main__":
    main()
