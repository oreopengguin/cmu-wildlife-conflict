"""
Figure 4 — Coexistence Risk Index and independent validation.
(a) Unified CRI map with top emergent-conflict hotspots.
(b) Observed (GBIF past->recent) vs OT-predicted latitudinal range shift.
(c) Permutation null: friction vs realized human-interface occurrence.
(d) Species-resolved risk decomposition (standardized signal heatmap).
"""
from __future__ import annotations
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import pearsonr
import config as C
import figstyle as FS
import figdata as FD
from build_covariates import lonlat_to_rc

FS.apply()

# a few reference cities for context on the risk map
CITIES = {"Paris": (2.35, 48.85), "Berlin": (13.4, 52.52), "Rome": (12.5, 41.9),
          "Madrid": (-3.7, 40.4), "Warsaw": (21.0, 52.23), "Bucharest": (26.1, 44.4),
          "Kyiv": (30.5, 50.45)}


def panel_a(ax, A):
    mask = A["mask"]; lons = A["lons"]; lats = A["lats"]
    cri = A["CRI"]
    FS.sea(ax, mask, lons, lats)
    cn = np.where(mask, cri, np.nan)
    im = FS.imshow_map(ax, cn, lons, lats, FS.EMBER,
                       vmin=np.nanpercentile(cn, 3), vmax=np.nanpercentile(cn, 99))
    FS.coastline_from_mask(ax, mask, lons, lats, lw=0.4)
    # top hotspot cells
    ny, nx = mask.shape
    flat = np.nan_to_num(cn, nan=-1e9).ravel()
    top = np.argsort(flat)[-10:]
    for t in top:
        r, c = t // nx, t % nx
        ax.plot(lons[c], lats[r], marker="*", mfc="#ffe9a8", mec=FS.INK,
                ms=9, mew=0.7)
    for nm, (lo, la) in CITIES.items():
        ax.plot(lo, la, "o", ms=2.2, color=FS.INK)
        ax.text(lo + 0.3, la + 0.3, nm, fontsize=5.6, color=FS.INK)
    FS.map_axes(ax, lons, lats)
    FS.cbar(ax.figure, im, ax, "Coexistence Risk Index (z)")
    ax.set_title("Emergent human–wildlife conflict risk (2081–2100)", loc="left")
    ax.text(0.015, 0.02,
            "CRI = z(friction) + 0.8·z(current × human) + 0.8·z(gain into human land)\n"
            "z = standardized (z-score)",
            transform=ax.transAxes, va="bottom", ha="left", fontsize=5.0, color=FS.INK,
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=FS.FAINT, lw=0.4, alpha=0.72))


def panel_b(ax, A):
    s = FD.load_summary()
    sps = FD.species_present(A)
    xs, ys, cols, labs = [], [], [], []
    for sp in sps:
        r = s["species"][sp]
        if r["observed_shift"] is None:
            continue
        xs.append(r["observed_shift"]["d_lat"])
        ys.append(r["predicted_shift"]["d_lat"])
        cols.append(C.SPECIES_COLOR[sp]); labs.append(C.SPECIES_COMMON[sp])
    xs = np.array(xs); ys = np.array(ys)
    lim = np.array([min(xs.min(), ys.min()), max(xs.max(), ys.max())])
    pad = 0.1 * (lim[1] - lim[0] + 1e-9)
    lim = lim + np.array([-pad, pad])
    ax.axhline(0, color=FS.FAINT, lw=0.6); ax.axvline(0, color=FS.FAINT, lw=0.6)
    ax.plot(lim, lim, color=FS.MUTE, lw=0.9, ls="--", label="1:1")
    for x, y, c, l in zip(xs, ys, cols, labs):
        ax.scatter(x, y, s=55, color=c, edgecolor=FS.INK, linewidth=0.5, zorder=3)
        ax.annotate(l, (x, y), fontsize=6, xytext=(4, 3),
                    textcoords="offset points", color=FS.INK)
    if len(xs) >= 3:
        from scipy.stats import spearmanr
        r, p = pearsonr(xs, ys)
        rho, _ = spearmanr(xs, ys)
        n_pole = int(np.sum(xs > 0))
        ax.text(0.04, 0.96,
                f"Spearman ρ = {rho:.2f}   Pearson r = {r:.2f}\n"
                f"{n_pole}/{len(xs)} taxa shifted poleward, as predicted\n"
                f"Grey wolf: recolonization-driven outlier",
                transform=ax.transAxes, va="top", fontsize=6.9,
                bbox=dict(boxstyle="round,pad=0.35", fc="#f4f6f9", ec=FS.FAINT, lw=0.6))
    ax.set_xlabel(r"Observed $\Delta$latitude, 1990–2007 $\rightarrow$ 2008–2026 (°)")
    ax.set_ylabel("OT-predicted Δlatitude (°)")
    ax.set_title("Validation: predicted vs observed range shift", loc="left")


def panel_c(ax, A):
    mask = A["mask"]; H = A["H"]; nx = int(A["nx"]); ny = int(A["ny"])
    F = A["comm_friction"]
    occ = FD.load_all_occ()
    rec = occ[occ.year >= 2015]
    r, c = lonlat_to_rc(rec.lon.values, rec.lat.values)
    inb = (r >= 0) & (r < ny) & (c >= 0) & (c < nx)
    occ_cells = set((r[inb] * nx + c[inb]).tolist())
    human = mask & (H > 0.4)
    hy, hx = np.where(human)
    flat = hy * nx + hx
    label = np.array([1.0 if f in occ_cells else 0.0 for f in flat])
    fr = F[hy, hx]
    ok = np.isfinite(fr)
    fr, label = fr[ok], label[ok]
    # observed association (point-biserial ~ mean difference standardized)
    def assoc(fvals, lab):
        m1 = fvals[lab == 1].mean(); m0 = fvals[lab == 0].mean()
        return (m1 - m0) / (fvals.std() + 1e-9)
    obs = assoc(fr, label)
    rng = np.random.default_rng(1)
    null = np.array([assoc(fr, rng.permutation(label)) for _ in range(2000)])
    ax.hist(null, bins=40, color="#c7ccd4", edgecolor="white", linewidth=0.3,
            label="null (label-permuted)")
    ax.axvline(obs, color="#d64545", lw=3.2, label="observed", solid_capstyle="round")
    ax.annotate("observed", xy=(obs, 0.5), xytext=(obs - 0.03, 0.63),
                xycoords=ax.get_xaxis_transform(), textcoords=ax.get_xaxis_transform(),
                fontsize=6.6, color="#d64545", fontweight="bold", ha="right",
                arrowprops=dict(arrowstyle="->", color="#d64545", lw=1.0))
    ax.legend(loc="upper left", fontsize=6.4, frameon=False)
    p = (np.sum(null >= obs) + 1) / (len(null) + 1)
    ax.text(0.96, 0.94, f"observed = {obs:.2f}\npermutation p = {p:.3g}\n"
            f"({int(label.sum())} interface cells)",
            transform=ax.transAxes, ha="right", va="top", fontsize=7.2,
            color=FS.INK,
            bbox=dict(boxstyle="round,pad=0.35", fc="#fff4f4", ec="#d64545", lw=0.6))
    ax.set_xlabel("standardized friction–interface association")
    ax.set_ylabel("null frequency")
    ax.set_title("Friction predicts realized interface (permutation test)", loc="left")


def panel_d(ax, A):
    s = FD.load_summary(); sps = FD.species_present(A)
    metrics = ["W_shift_km", "Δfragmentation", "topo_change_W1",
               "mean_friction", "interface_AUC"]
    M = np.full((len(sps), len(metrics)), np.nan)
    for i, sp in enumerate(sps):
        r = s["species"][sp]
        M[i, 0] = r["W_shift_km"]
        M[i, 1] = r["frag_future"]["n_patches"] - r["frag_present"]["n_patches"]
        M[i, 2] = r["topo_change_W1"]
        fr = A[f"friction__{sp}"]
        M[i, 3] = np.nanmean(fr[np.isfinite(fr) & (fr > 0)]) if np.isfinite(fr).any() else np.nan
        M[i, 4] = r["interface"]["auc_friction"] if r["interface"] else np.nan
    # z-score columns for comparability
    Z = (M - np.nanmean(M, axis=0)) / (np.nanstd(M, axis=0) + 1e-9)
    im = ax.imshow(Z, aspect="auto", cmap=FS.DIVSHIFT, vmin=-2, vmax=2)
    ax.set_xticks(range(len(metrics)))
    ax.set_xticklabels(["W-shift", "Δpatches", "topo shift", "friction", "IV-AUC"],
                       rotation=30, ha="right", fontsize=6.6)
    ax.set_yticks(range(len(sps)))
    ax.set_yticklabels([C.SPECIES_COMMON[sp] for sp in sps], fontsize=7)
    for i in range(len(sps)):
        for j in range(len(metrics)):
            if np.isfinite(M[i, j]):
                v = M[i, j]
                txt = f"{v:.0f}" if abs(v) >= 10 else f"{v:.2f}"
                ax.text(j, i, txt, ha="center", va="center", fontsize=5.6,
                        color=FS.INK)
    FS.cbar(ax.figure, im, ax, "z-score across species")
    ax.set_title("Per-species risk decomposition", loc="left")
    ax.tick_params(length=0)


def main():
    A = FD.load_analysis()
    fig = plt.figure(figsize=(11.0, 9.4))
    gs = fig.add_gridspec(2, 2, hspace=0.30, wspace=0.22,
                          left=0.07, right=0.955, top=0.93, bottom=0.08)
    axa = fig.add_subplot(gs[0, 0]); panel_a(axa, A); FS.panel_label(axa, "a")
    axb = fig.add_subplot(gs[0, 1]); panel_b(axb, A); FS.panel_label(axb, "b")
    axc = fig.add_subplot(gs[1, 0]); panel_c(axc, A); FS.panel_label(axc, "c")
    axd = fig.add_subplot(gs[1, 1]); panel_d(axd, A); FS.panel_label(axd, "d")
    fig.suptitle("Figure 4  |  Coexistence Risk Index and out-of-sample validation",
                 x=0.07, ha="left", fontsize=11, fontweight="bold")
    fig.savefig(C.FIGDIR / "figure4_risk_validation.png", bbox_inches="tight")
    fig.savefig(C.FIGDIR / "figure4_risk_validation.pdf", bbox_inches="tight")
    print("saved figure4")


if __name__ == "__main__":
    main()
