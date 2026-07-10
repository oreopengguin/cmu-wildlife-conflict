"""
Figure 1 — The Framework & Data.
(a) Multi-species occurrence density over Europe + target-group effort.
(b) Environmental niche space (PCA of bioclim): background cloud + species KDEs.
(c) The Gibbs -> PPP -> OT -> topology -> risk pipeline schematic.
(d) Spatial cross-validation skill (AUC / Boyce / TSS) per species.
"""
from __future__ import annotations
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from scipy.stats import gaussian_kde
from sklearn.decomposition import PCA
import config as C
import figstyle as FS
import figdata as FD

FS.apply()


def panel_a(ax, A):
    mask = A["mask"]; lons = A["lons"]; lats = A["lats"]
    occ = FD.load_all_occ()
    FS.sea(ax, mask, lons, lats)
    # 2D histogram of all occurrences (log density)
    H, xe, ye = np.histogram2d(occ.lon, occ.lat, bins=[160, 120],
                               range=[[lons[0], lons[-1]], [lats[-1], lats[0]]])
    H = np.log10(H.T + 1)
    im = ax.imshow(H, extent=[lons[0], lons[-1], lats[-1], lats[0]],
                   origin="lower", cmap=FS.SUIT, interpolation="nearest",
                   vmax=np.percentile(H[H > 0], 99))
    FS.coastline_from_mask(ax, mask, lons, lats, lw=0.4)
    FS.map_axes(ax, lons, lats)
    FS.add_scalebar(ax, lons, lats, 500)
    FS.cbar(ax.figure, im, ax, "log$_{10}$(occurrences + 1)")
    ax.set_title("Georeferenced records across 7 conflict-prone taxa", loc="left")
    n = len(occ)
    ax.text(0.02, 0.02, f"n = {n:,} occurrences", transform=ax.transAxes,
            fontsize=7, color="#f6efc0", va="bottom", fontweight="bold")


def panel_b(ax, A):
    mask = A["mask"]
    # Build env space from processed predictor stack
    d = np.load(C.DATA_PROC / "dataset.npz", allow_pickle=True)
    Pz = d["Pz"]; nx = int(d["nx"])
    land = np.flatnonzero(mask.ravel())
    X = Pz.reshape(Pz.shape[0], -1)[:, land].T
    rng = np.random.default_rng(0)
    sub = rng.choice(len(X), size=min(6000, len(X)), replace=False)
    pca = PCA(n_components=2).fit(X[sub])
    Y = pca.transform(X)
    ax.scatter(Y[sub, 0], Y[sub, 1], s=2, c="#d7dce3", alpha=0.5, lw=0,
               rasterized=True)
    # per-species niche KDE contours
    for sp in FD.species_present(A):
        cells = d[f"pres__{sp}"]
        r = cells // nx; c = cells % nx
        Xi = Pz[:, r, c].T
        Yi = pca.transform(Xi)
        if len(Yi) < 40:
            continue
        try:
            k = gaussian_kde(Yi[:, :2].T)
        except Exception:
            continue
        xx, yy = np.mgrid[Y[:, 0].min():Y[:, 0].max():80j,
                          Y[:, 1].min():Y[:, 1].max():80j]
        zz = k(np.vstack([xx.ravel(), yy.ravel()])).reshape(xx.shape)
        ax.contour(xx, yy, zz, levels=[zz.max() * 0.4], colors=[C.SPECIES_COLOR[sp]],
                   linewidths=1.6, alpha=0.95)
        # redundant shape encoding: species marker at niche centroid
        ax.scatter(Yi[:, 0].mean(), Yi[:, 1].mean(), marker=C.SPECIES_MARKER[sp],
                   s=46, facecolor=C.SPECIES_COLOR[sp], edgecolor="white",
                   linewidth=0.8, zorder=5)
    # legend proxies (colour + shape together)
    for sp in FD.species_present(A):
        ax.scatter([], [], color=C.SPECIES_COLOR[sp], marker=C.SPECIES_MARKER[sp],
                   s=34, label=C.SPECIES_COMMON[sp])
    ax.legend(loc="upper left", ncol=1, fontsize=6.3, handlelength=1.0,
              borderaxespad=0.2)
    ev = pca.explained_variance_ratio_ * 100
    ax.set_xlabel(f"Climate PC1 ({ev[0]:.0f}%)")
    ax.set_ylabel(f"Climate PC2 ({ev[1]:.0f}%)")
    ax.set_title("Realized climatic niches (bioclim PCA)", loc="left")


def panel_c(ax):
    ax.axis("off")
    ax.set_xlim(0, 10); ax.set_ylim(0, 10)
    steps = [
        ("Presence-only\nrecords (GBIF)", 0.6, "#123a5e"),
        ("MaxEnt / Gibbs\n= Poisson PPP", 2.55, "#1f7a7a"),
        ("Present & future\nsuitability", 4.5, "#5fae57"),
        ("Entropic optimal\ntransport", 6.45, "#8c2d62"),
        ("Coexistence\nRisk Index", 8.4, "#d64545"),
    ]
    y = 6.7
    for (txt, x, col) in steps:
        box = FancyBboxPatch((x, y), 1.7, 1.7, boxstyle="round,pad=0.06,rounding_size=0.16",
                             linewidth=1.1, edgecolor=col, facecolor=FS.to_rgba(col, 0.10))
        ax.add_patch(box)
        ax.text(x + 0.85, y + 0.85, txt, ha="center", va="center", fontsize=6.6,
                color=FS.INK, fontweight="bold")
    for i in range(len(steps) - 1):
        x0 = steps[i][1] + 1.7; x1 = steps[i + 1][1]
        ar = FancyArrowPatch((x0, y + 0.85), (x1, y + 0.85),
                             arrowstyle="-|>", mutation_scale=9,
                             lw=1.1, color=FS.MUTE)
        ax.add_patch(ar)
    # lower row: the three geometric analyses feeding the CRI
    geo = [("Optimal transport\ndisplacement field", 2.0, "#8c2d62"),
           ("Spectral circuit\nconnectivity", 4.4, "#1e88c9"),
           ("Persistent\nhomology", 6.8, "#5e3c99")]
    yy = 2.7
    for (txt, x, col) in geo:
        box = FancyBboxPatch((x, yy), 1.9, 1.5, boxstyle="round,pad=0.05,rounding_size=0.14",
                             linewidth=1.0, edgecolor=col, facecolor=FS.to_rgba(col, 0.10))
        ax.add_patch(box)
        ax.text(x + 0.95, yy + 0.75, txt, ha="center", va="center", fontsize=6.3,
                color=FS.INK)
        ar = FancyArrowPatch((x + 0.95, yy + 1.5), (8.4 + 0.85, 6.7),
                             arrowstyle="-|>", mutation_scale=7, lw=0.8,
                             color=FS.FAINT, connectionstyle="arc3,rad=-0.15")
        ax.add_patch(ar)
    ax.text(0.2, 9.5, "A mechanistic, conflict-data-free pipeline", fontsize=8.2,
            fontweight="bold")
    ax.text(0.2, 0.6, r"$p(x)\propto e^{\beta\cdot f(x)}\;\Rightarrow\;"
            r"\min_P\langle P,C\rangle-\varepsilon H(P)\;\Rightarrow\;"
            r"F(x)=\langle T(x),\nabla H\rangle_+$",
            fontsize=7.2, color=FS.MUTE)


def panel_d(ax):
    m = FD.load_metrics()
    sps = [sp for sp in C.SPECIES_NAMES if sp in m]
    yy = np.arange(len(sps))[::-1]
    # TSS removed: it is threshold-dependent and ill-suited to presence-only
    # data; we report AUC and the presence-only Boyce index (see CHANGES.md).
    for metric, off, mk, lab in [("auc", 0.14, "o", "AUC"),
                                 ("boyce", -0.14, "s", "Boyce index")]:
        vals = [m[sp][metric][0] for sp in sps]
        errs = [m[sp][metric][1] for sp in sps]
        col = {"auc": "#0072B2", "boyce": "#009E73"}[metric]
        ax.errorbar(vals, yy + off, xerr=errs, fmt=mk, ms=5.0, color=col,
                    ecolor=FS.to_rgba(col, 0.5), elinewidth=1.0, capsize=2,
                    label=lab, lw=0)
    ax.axvline(0.5, color=FS.FAINT, lw=0.8, ls="--")
    ax.text(0.5, 0.015, "random", fontsize=6, color=FS.MUTE, ha="center",
            va="bottom", transform=ax.get_xaxis_transform())
    ax.set_yticks(yy)
    ax.set_yticklabels([C.SPECIES_COMMON[sp] for sp in sps], fontsize=7)
    ax.set_xlabel("Spatial cross-validation skill")
    ax.set_xlim(-0.05, 1.02)
    ax.legend(loc="lower right", ncol=2, fontsize=6.6, columnspacing=0.8)
    ax.set_title("Block-CV performance (mean ± SD, 4 folds)", loc="left")
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)


def main():
    A = FD.load_analysis()
    fig = plt.figure(figsize=(11.0, 9.2))
    gs = fig.add_gridspec(2, 2, hspace=0.26, wspace=0.20,
                          left=0.055, right=0.965, top=0.93, bottom=0.06)
    axa = fig.add_subplot(gs[0, 0]); panel_a(axa, A); FS.panel_label(axa, "a")
    axb = fig.add_subplot(gs[0, 1]); panel_b(axb, A); FS.panel_label(axb, "b")
    axc = fig.add_subplot(gs[1, 0]); panel_c(axc); FS.panel_label(axc, "c")
    axd = fig.add_subplot(gs[1, 1]); panel_d(axd); FS.panel_label(axd, "d")
    fig.suptitle("Figure 1  |  A geometry-of-coexistence framework for European "
                 "human–wildlife interaction", x=0.055, ha="left",
                 fontsize=11, fontweight="bold")
    fig.savefig(C.FIGDIR / "figure1_framework.png", bbox_inches="tight")
    fig.savefig(C.FIGDIR / "figure1_framework.pdf", bbox_inches="tight")
    print("saved figure1")


if __name__ == "__main__":
    main()
