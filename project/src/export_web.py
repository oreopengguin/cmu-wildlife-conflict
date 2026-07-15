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
import geolabels as GL

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
    """Realized climatic niches as Gaussian-KDE density contours in bioclim-PCA
    space — the SAME construction as Figure 1B (a single isoline at 0.4*max per
    species), so the interactive chart and the flagship figure match exactly."""
    from scipy.stats import gaussian_kde
    d = np.load(C.DATA_PROC / "dataset.npz", allow_pickle=True)
    Pz = d["Pz"]; nx = int(d["nx"]); mask = A["mask"]
    land = np.flatnonzero(mask.ravel())
    X = Pz.reshape(Pz.shape[0], -1)[:, land].T
    rng = np.random.default_rng(0)
    # PCA fit on a 6000-cell sample (matches figure 1B's fit)
    fitsub = rng.choice(len(X), size=min(6000, len(X)), replace=False)
    pca = PCA(n_components=2).fit(X[fitsub])
    Yall = pca.transform(X)
    # orient PC1 so higher = warmer (positive correlation with BIO1, the first
    # standardized predictor) — keeps the "-> warmer / drier" axis label honest
    if np.corrcoef(Yall[:, 0], X[:, 0])[0, 1] < 0:
        pca.components_[0] *= -1
        Yall = pca.transform(X)
    bgsub = rng.choice(len(X), size=min(2200, len(X)), replace=False)
    bg = Yall[bgsub]
    xmin, xmax = float(Yall[:, 0].min()), float(Yall[:, 0].max())
    ymin, ymax = float(Yall[:, 1].min()), float(Yall[:, 1].max())

    species = {}
    for sp in FD.species_present(A):
        cells = d[f"pres__{sp}"]; r = cells // nx; c = cells % nx
        Yi = pca.transform(Pz[:, r, c].T)
        if len(Yi) < 40:
            continue
        try:
            k = gaussian_kde(Yi[:, :2].T)
        except Exception:
            continue
        xx, yy = np.mgrid[xmin:xmax:80j, ymin:ymax:80j]
        zz = k(np.vstack([xx.ravel(), yy.ravel()])).reshape(xx.shape)
        lev = float(zz.max() * 0.4)                      # identical level to fig1B
        fig = plt.figure(); ax = fig.add_subplot(111)
        cs = ax.contour(xx, yy, zz, levels=[lev])
        try:
            segs = cs.allsegs[0]
        except Exception:
            segs = [p.vertices for p in cs.get_paths()]
        paths = []
        for seg in segs:
            seg = np.asarray(seg)
            if len(seg) >= 6:
                paths.append([[round(float(a), 3), round(float(b), 3)] for a, b in seg])
        plt.close(fig)
        ctr = [round(float(Yi[:, 0].mean()), 3), round(float(Yi[:, 1].mean()), 3)]
        species[sp] = {"centroid": ctr, "contours": paths, "n": int(len(cells))}

    out = {"pc1var": round(float(pca.explained_variance_ratio_[0] * 100)),
           "pc2var": round(float(pca.explained_variance_ratio_[1] * 100)),
           "background": [[round(float(a), 2), round(float(b), 2)] for a, b in bg],
           "species": species}
    (DATA / "niche.json").write_text(json.dumps(out))
    print(f"wrote niche.json ({sum(len(v['contours']) for v in species.values())} contour paths)")


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


def export_fig2c(A):
    """Interactive Figure 2c: per-species median required range-shift vs latitude
    — the exact series fig2.py::panel_c draws as coloured trend lines."""
    sps = FD.species_present(A)
    mask = A["mask"]; lats = A["lats"]
    LAT = np.meshgrid(A["lons"], lats)[1]
    bins = np.linspace(lats[-1], lats[0], 12)
    ctr = 0.5 * (bins[1:] + bins[:-1])
    species, ymax = [], 0.0
    for sp in sps:
        s = A[f"shift__{sp}"]; p = A[f"present__{sp}"]
        ok = mask & np.isfinite(s) & (np.nan_to_num(p) > np.nanpercentile(p, 60))
        xx = LAT[ok]; yy = s[ok]
        pts = []
        for i in range(len(bins) - 1):
            sel = (xx >= bins[i]) & (xx < bins[i + 1])
            if sel.sum() > 20:
                m = float(np.median(yy[sel]))
                pts.append([round(float(ctr[i]), 2), round(m, 1)])
                ymax = max(ymax, m)
        species.append({"key": sp, "common": C.SPECIES_COMMON[sp],
                        "color": C.SPECIES_COLOR[sp], "marker": C.SPECIES_MARKER[sp],
                        "points": pts})
    out = {"lat_min": round(float(lats[-1]), 1), "lat_max": round(float(lats[0]), 1),
           "shift_max": round(ymax, 0), "species": species}
    (DATA / "fig2c.json").write_text(json.dumps(out))
    print("wrote fig2c.json")


def export_fig3b(A):
    """Interactive Figure 3b: conflict-corridor field (current × human pressure)
    with the top-16 pinch-points — the exact circles fig3.py::panel_b marks."""
    from scipy.ndimage import maximum_filter
    mask = A["mask"]; lons = A["lons"]; lats = A["lats"]
    corridor = np.where(mask, A["current"] * np.clip(A["H"], 0, 1), np.nan)
    pos = corridor[np.isfinite(corridor) & (corridor > 0)]
    vmax = float(np.percentile(pos, 97))
    # clean background PNG (EMBER, transparent sea) — matches the figure's panel b
    f = np.clip(corridor / (vmax + 1e-9), 0, 1); f = np.where(mask, f, np.nan)
    ny, nx = mask.shape
    fig = plt.figure(figsize=(nx / 100, ny / 100), dpi=150)
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off")
    ax.imshow(f, cmap=FS.EMBER, vmin=0, vmax=1, interpolation="bilinear")
    ax.contour(mask.astype(float), levels=[0.5], colors=["#0b1220"], linewidths=0.5, alpha=0.6)
    fig.savefig(IMG / "corridor_map.png", transparent=True, dpi=150); plt.close(fig)
    # coarse intensity grid for hover-anywhere
    cf = 3
    cc, cm = coarsen(corridor, mask, cf)
    ccv = np.clip(np.nan_to_num(cc) / (vmax + 1e-9), 0, 1)
    # pinch-points = top-16 local maxima of the corridor field (as in fig3.py)
    cf0 = np.nan_to_num(corridor)
    loc = maximum_filter(cf0, size=11)
    thr = float(np.percentile(pos, 92))
    pk = (cf0 == loc) & (cf0 > thr)
    ys, xs = np.where(pk)
    order = np.argsort(cf0[ys, xs])[-16:][::-1]            # highest intensity first
    circles = []
    for rank, k in enumerate(order, 1):
        yy, xx = int(ys[k]), int(xs[k])
        la, lo = float(lats[yy]), float(lons[xx])
        circles.append({"lon": round(lo, 2), "lat": round(la, 2),
                        "intensity": round(float(corridor[yy, xx]), 3),
                        "rel": round(float(corridor[yy, xx] / (vmax + 1e-9) * 100)),
                        "rank": rank, "place": GL.place_label(la, lo)})
    out = {"extent": [float(lons[0]), float(lons[-1]), float(lats[-1]), float(lats[0])],
           "coarse_shape": list(cm.shape), "mask": _b64_u8(cm.ravel()),
           "grid": _b64_u8(np.round(ccv.ravel() * 100)), "vmax": round(vmax, 3),
           "circles": circles}
    (DATA / "fig3b.json").write_text(json.dumps(out))
    print(f"wrote fig3b.json ({len(circles)} pinch-points) + corridor_map.png")


def export_fig4a(A):
    """Named bright clusters on the CRI map — declustered local maxima of the
    committed CRI field, each labelled by landmark / nearest city / region."""
    from scipy.ndimage import maximum_filter
    mask = A["mask"]; cri = A["CRI"]; lons = A["lons"]; lats = A["lats"]
    LON, LAT = np.meshgrid(lons, lats)
    valid = mask & np.isfinite(cri)
    cn = np.where(valid, cri, -1e9)
    loc = maximum_filter(cn, size=9)
    v = cri[valid]
    thr = float(np.percentile(v, 92))
    ys, xs = np.where((cn == loc) & (cn > thr))
    vals = cn[ys, xs]
    order = np.argsort(vals)[::-1]

    def area_mean(la, lo, km=150.0):
        """Mean CRI within km of a point — a peak is only a genuine bright
        cluster (not an isolated single-cell spike) if its surroundings are
        also elevated."""
        p1 = np.radians(la); dphi = np.radians(LAT - la); dl = np.radians(LON - lo)
        a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(np.radians(LAT)) * np.sin(dl / 2) ** 2
        d = 2 * 6371.0 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))
        m = valid & (d <= km)
        return float(np.nanmean(cri[m])) if m.any() else -1e9

    labels, kept = [], []
    for i in order:
        la, lo = float(LAT[ys[i], xs[i]]), float(LON[ys[i], xs[i]])
        # skip cells near the domain edge (extrapolated / outside the European focus,
        # e.g. the thin North-African strip) and lone spikes in otherwise-dim regions
        if not (35.6 <= la <= 70.5 and -10.5 <= lo <= 38.5):
            continue
        if area_mean(la, lo) < 0.4:
            continue
        if any(GL._haversine_km(la, lo, k[0], k[1]) < 230 for k in kept):
            continue                                   # decluster (>=230 km apart)
        name = GL.map_label(la, lo)
        if any(l["name"] == name for l in labels):     # avoid duplicate names
            continue
        kept.append((la, lo))
        labels.append({"name": name, "lon": round(lo, 2), "lat": round(la, 2),
                       "cri": round(float(vals[i]), 1)})
        if len(labels) >= 11:
            break
    extent = [float(lons[0]), float(lons[-1]), float(lats[-1]), float(lats[0])]
    (DATA / "fig4a.json").write_text(json.dumps({"extent": extent, "labels": labels}))
    print(f"wrote fig4a.json ({len(labels)} bright-cluster labels)")


def export_fig4d(A):
    """Interactive Figure 4d: per-species risk decomposition — the exact five
    signals fig4.py::panel_d tabulates (raw values + across-species z-scores)."""
    s = FD.load_summary(); sps = FD.species_present(A)
    labels = ["W-shift (km)", "Δpatches", "topo shift", "mean friction", "interface AUC"]
    rows, M = [], []
    for sp in sps:
        r = s["species"][sp]
        fr = A[f"friction__{sp}"]
        mf = float(np.nanmean(fr[np.isfinite(fr) & (fr > 0)])) if np.isfinite(fr).any() else np.nan
        vals = [float(r["W_shift_km"]),
                float(r["frag_future"]["n_patches"] - r["frag_present"]["n_patches"]),
                float(r["topo_change_W1"]), mf,
                float(r["interface"]["auc_friction"]) if r["interface"] else np.nan]
        M.append(vals)
        rows.append({"key": sp, "common": C.SPECIES_COMMON[sp],
                     "color": C.SPECIES_COLOR[sp], "marker": C.SPECIES_MARKER[sp]})
    M = np.array(M, float)
    Z = (M - np.nanmean(M, axis=0)) / (np.nanstd(M, axis=0) + 1e-9)
    for i, rr in enumerate(rows):
        rr["vals"] = [None if not np.isfinite(v) else round(float(v), 3) for v in M[i]]
        rr["z"] = [None if not np.isfinite(z) else round(float(z), 2) for z in Z[i]]
    out = {"metrics": labels, "species": rows}
    (DATA / "fig4d.json").write_text(json.dumps(out))
    print("wrote fig4d.json")


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
    export_fig2c(A)
    export_fig3b(A)
    export_fig4a(A)
    export_fig4d(A)
    copy_figures()
    print("== web export complete ==")


if __name__ == "__main__":
    main()
