"""
Per-species Coexistence Risk Index.

Runs the EXACT same recipe as the community CRI (risk.coexistence_risk, same
0.8/0.8 weights; connectivity.solve_current, same resistance formula) but once
per species instead of on the community-aggregated suitability. Produces 7
individual CRI maps so one can see *which species drives each hotspot*.

IMPORTANT (honesty): the community CRI aggregates the *ingredients* (suitability)
first and then builds the index, so these 7 per-species maps do NOT average back
to the community map — they are a separate, per-species run of the same recipe.

Outputs:
  results/species_cri.npz          (cri__<species> maps, mask, lons, lats)
  website/assets/img/cri/<key>.png (EMBER maps, per-species percentile stretch)
  website/assets/data/cri_species.json (coarse per-species CRI grids for hover)
"""
from __future__ import annotations
import json, base64
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import config as C
import figstyle as FS
import figdata as FD
import connectivity as CN
import risk as RK

WEB = C.ROOT / "website"
IMG = WEB / "assets" / "img" / "cri"
DATA = WEB / "assets" / "data"
for d in (IMG, DATA):
    d.mkdir(parents=True, exist_ok=True)
FS.apply()


def _b64_u8(a):
    return base64.b64encode(np.asarray(a, dtype=np.uint8).tobytes()).decode()


def coarsen(field, mask, cf):
    ny, nx = field.shape
    ny2, nx2 = (ny // cf) * cf, (nx // cf) * cf
    f = np.where(mask, field, np.nan)[:ny2, :nx2].reshape(ny2 // cf, cf, nx2 // cf, cf)
    m = mask[:ny2, :nx2].reshape(ny2 // cf, cf, nx2 // cf, cf)
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        cval = np.nanmean(f, axis=(1, 3))
    return cval, (m.mean(axis=(1, 3)) >= 0.5)


def render(cri, mask, path):
    """EMBER map with per-species 3rd–99th percentile stretch (same style as the
    community risk_map.png). Returns (lo, hi) used, for the coarse grid."""
    v = cri[mask & np.isfinite(cri)]
    lo, hi = np.percentile(v, 3), np.percentile(v, 99)
    f = np.where(mask, np.clip((cri - lo) / (hi - lo + 1e-9), 0, 1), np.nan)
    ny, nx = mask.shape
    fig = plt.figure(figsize=(nx / 100, ny / 100), dpi=150)
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off")
    ax.imshow(f, cmap=FS.EMBER, vmin=0, vmax=1, interpolation="bilinear")
    ax.contour(mask.astype(float), levels=[0.5], colors=["#0b1220"], linewidths=0.5, alpha=0.6)
    fig.savefig(path, transparent=True, dpi=150); plt.close(fig)
    return lo, hi


def main():
    A = FD.load_analysis()
    mask = A["mask"]; H = A["H"]; lons = A["lons"]; lats = A["lats"]
    species = FD.species_present(A)
    store = {"mask": mask, "lons": lons, "lats": lats}
    cf = 3
    _, cmask = coarsen(A[f"present__{species[0]}"], mask, cf)
    grids = {"extent": [float(lons[0]), float(lons[-1]), float(lats[-1]), float(lats[0])],
             "coarse_shape": list(cmask.shape), "mask": _b64_u8(cmask.ravel()),
             "species": {}}
    summary = {}
    for sp in species:
        present = A[f"present__{sp}"]; future = A[f"future__{sp}"]
        friction = A[f"friction__{sp}"]
        # per-species connectivity current — SAME resistance + solve as community
        R = CN.resistance_surface(present, H, mask)
        cur = CN.solve_current(present, future, R, mask)["current"]
        # per-species CRI — SAME function + weights as community
        cri, _ = RK.coexistence_risk(friction, cur, present, future, H, mask)
        store[f"cri__{sp}"] = cri.astype("float32")

        key = sp.replace(" ", "_")
        lo, hi = render(cri, mask, IMG / f"{key}.png")
        cc, _ = coarsen(np.clip((cri - lo) / (hi - lo + 1e-9), 0, 1), mask, cf)
        grids["species"][sp] = {"cri": _b64_u8(np.nan_to_num(cc).ravel() * 100)}

        # honest top-cell readout for CHANGES / interpretation
        flat = np.where(mask & np.isfinite(cri), cri, -1e9).ravel()
        t = int(np.argmax(flat)); ny, nx = mask.shape
        summary[sp] = dict(common=C.SPECIES_COMMON[sp],
                           top_lon=round(float(lons[t % nx]), 1),
                           top_lat=round(float(lats[t // nx]), 1))
        print(f"[cri] {C.SPECIES_COMMON[sp]:14s} peak at "
              f"{summary[sp]['top_lat']}N,{summary[sp]['top_lon']}E")

    np.savez_compressed(C.RESULTS / "species_cri.npz", **store)
    (DATA / "cri_species.json").write_text(json.dumps(grids))
    print("[cri] saved results/species_cri.npz, per-species PNGs, cri_species.json")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
