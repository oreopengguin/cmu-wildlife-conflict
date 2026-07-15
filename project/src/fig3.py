"""
Figure 3 — Spectral connectivity & topological fragmentation.
(a) Resistance landscape with circuit current-flow corridors.
(b) Pinch-point (bottleneck) map — where movement is squeezed through people.
(c) Persistence diagrams (H0/H1) present vs future for the community surface.
(d) Persistence landscapes + persistence-based fragmentation index change.
"""
from __future__ import annotations
import numpy as np
import matplotlib.pyplot as plt
import config as C
import figstyle as FS
import figdata as FD
import topology as TP

FS.apply()


def panel_a(ax, A):
    mask = A["mask"]; lons = A["lons"]; lats = A["lats"]
    R = A["resistance"]; cur = A["current"]
    FS.sea(ax, mask, lons, lats)
    # resistance as muted background
    Rn = np.where(mask, R, np.nan)
    FS.imshow_map(ax, Rn, lons, lats, plt.cm.Greys,
                  vmin=np.nanpercentile(Rn, 2), vmax=np.nanpercentile(Rn, 98),
                  alpha=0.55)
    cn = np.where(mask, cur, np.nan)
    im = FS.imshow_map(ax, np.where(cn > np.nanpercentile(cn, 55), cn, np.nan),
                       lons, lats, FS.FLOW, vmax=np.nanpercentile(cn, 99))
    FS.coastline_from_mask(ax, mask, lons, lats, lw=0.4)
    FS.map_axes(ax, lons, lats)
    FS.cbar(ax.figure, im, ax, "movement current")
    ax.set_title("Climate-forced movement routed through landscape", loc="left")
    ax.text(0.015, 0.02, "landscape resistance\n"
            r"$R = \mathrm{base} + \alpha\,(1-\mathrm{suitability}) + \gamma\,(\mathrm{human\ modification})$",
            transform=ax.transAxes, va="bottom", ha="left", fontsize=5.6, color=FS.INK,
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=FS.FAINT, lw=0.4, alpha=0.72))


def panel_b(ax, A):
    """Conflict corridors: forced movement that funnels through human-dominated
    land (current x human modification), with pinch-points marked."""
    from scipy.ndimage import maximum_filter
    mask = A["mask"]; lons = A["lons"]; lats = A["lats"]
    corridor = np.where(mask, A["current"] * np.clip(A["H"], 0, 1), np.nan)
    FS.sea(ax, mask, lons, lats)
    vmax = np.nanpercentile(corridor[corridor > 0], 97)
    im = FS.imshow_map(ax, corridor, lons, lats, FS.EMBER, vmin=0, vmax=vmax)
    # pinch-points = local maxima of the conflict-corridor field
    cf = np.nan_to_num(corridor)
    loc = maximum_filter(cf, size=11)
    ny, nx = mask.shape
    thr = np.nanpercentile(corridor[corridor > 0], 92)
    pk = (cf == loc) & (cf > thr)
    ys, xs = np.where(pk)
    order = np.argsort(cf[ys, xs])[-16:]
    for k in order:
        ax.plot(lons[xs[k]], lats[ys[k]], "o", mfc="none", mec="#0a3d62",
                ms=8, mew=1.1)
    FS.coastline_from_mask(ax, mask, lons, lats, lw=0.4)
    FS.map_axes(ax, lons, lats)
    FS.cbar(ax.figure, im, ax, "conflict-corridor intensity")
    ax.set_title("Conflict corridors & pinch-points (current × human pressure)",
                 loc="left")
    ax.text(0.015, 0.02, "corridor = movement current × human pressure\n"
            r"current routed on $R = \mathrm{base} + \alpha\,(1-\mathrm{suitability}) + \gamma\,(\mathrm{human\ mod.})$",
            transform=ax.transAxes, va="bottom", ha="left", fontsize=5.6, color=FS.INK,
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=FS.FAINT, lw=0.4, alpha=0.72))


# Okabe-Ito colourblind-safe pair used for the epoch contrast in c & d.
_BLUE, _ORANGE = "#0072B2", "#D55E00"


def panel_c(ax, A):
    """Persistence diagram (single scatter): colour encodes the epoch
    (present = blue, future = orange) and marker shape the homology dimension
    (H0 patches = circle, H1 loops = triangle); the legend sits in the clear
    top-right corner."""
    from matplotlib.lines import Line2D
    dP0 = A["comm_pdiagP0"]; dF0 = A["comm_pdiagF0"]
    dP1 = A["comm_pdiagP1"]; dF1 = A["comm_pdiagF1"]
    # superlevel-set convention: a feature is born at HIGH suitability (its
    # peak) and dies at a LOWER value (merge) -> birth > death, below diagonal.
    def sc(d, color, marker, s=16, minpers=0.008):
        if len(d) == 0:
            return
        birth = np.maximum(d[:, 0], d[:, 1]); death = np.minimum(d[:, 0], d[:, 1])
        pers = birth - death
        keep = pers > minpers
        ax.scatter(birth[keep], death[keep], s=s,
                   facecolor=FS.to_rgba(color, 0.5), edgecolor=color,
                   linewidth=0.5, marker=marker, rasterized=True)
    # find data range for zoom
    allv = np.concatenate([d[:, :2].ravel() for d in (dP0, dF0, dP1, dF1)
                           if len(d)])
    hi = np.nanpercentile(allv, 99.5) if len(allv) else 0.3
    ax.plot([0, hi], [0, hi], color=FS.FAINT, lw=0.8, ls="--", zorder=0)
    sc(dP0, _BLUE, "o")
    sc(dF0, _ORANGE, "o")
    sc(dP1, _BLUE, "^", s=24)
    sc(dF1, _ORANGE, "^", s=24)
    ax.set_xlabel("birth — suitability at patch peak")
    ax.set_ylabel("death — suitability at merge")
    ax.set_title("Persistence diagram: shape of the range", loc="left")
    handles = [Line2D([0], [0], marker="s", ls="none", mfc=_BLUE, mec="none", ms=7, label="present"),
               Line2D([0], [0], marker="s", ls="none", mfc=_ORANGE, mec="none", ms=7, label="future"),
               Line2D([0], [0], marker="o", ls="none", mfc="none", mec=FS.INK, ms=6, label="H$_0$ patches"),
               Line2D([0], [0], marker="^", ls="none", mfc="none", mec=FS.INK, ms=6, label="H$_1$ loops")]
    ax.legend(handles=handles, loc="upper right", fontsize=6.2,
              handletextpad=0.4, labelspacing=0.4, borderpad=0.35, framealpha=0.85)
    ax.set_xlim(-0.01, hi * 1.05); ax.set_ylim(-0.01, hi * 1.05)
    ax.set_aspect("equal")
    ax.text(0.03, 0.96, "features far below the diagonal\n= persistent habitat cores",
            transform=ax.transAxes, va="top", fontsize=6.2, color=FS.MUTE)


def panel_d(ax, A):
    dP0 = {0: A["comm_pdiagP0"], 1: A["comm_pdiagP1"]}
    dF0 = {0: A["comm_pdiagF0"], 1: A["comm_pdiagF1"]}
    xs, LP = TP.persistence_landscape(dP0, dim=0, n_layers=4)
    _, LF = TP.persistence_landscape(dF0, dim=0, n_layers=4)
    for i in range(LP.shape[0]):
        ax.plot(xs, LP[i], color=_BLUE, lw=1.1, alpha=0.85 - i * 0.15)
        ax.plot(xs, LF[i], color=_ORANGE, lw=1.1, alpha=0.85 - i * 0.15, ls="-")
    ax.fill_between(xs, LP[0], color=_BLUE, alpha=0.10)
    ax.fill_between(xs, LF[0], color=_ORANGE, alpha=0.10)
    ax.plot([], [], color=_BLUE, label="present")
    ax.plot([], [], color=_ORANGE, label="future")
    ax.set_xlabel("suitability threshold")
    ax.set_ylabel(r"persistence landscape $\lambda_k$")
    ax.set_title("Topological simplification of habitat", loc="left")
    ax.legend(loc="upper right", fontsize=6.6)
    ax.set_xlim(0, 0.32)               # zoom to where the features live
    s = FD.load_summary()["community"]
    fp = s["frag_present"]; ff = s["frag_future"]
    arw = r"$\rightarrow$"
    txt = (f"patches (H$_0$): {fp['n_patches']} {arw} {ff['n_patches']}\n"
           f"loops (H$_1$): {fp['n_loops']} {arw} {ff['n_loops']}\n"
           f"total persistence: {fp['total_persistence']:.2f} {arw} "
           f"{ff['total_persistence']:.2f}")
    ax.text(0.03, 0.97, txt, transform=ax.transAxes, va="top", fontsize=6.6,
            color=FS.INK, bbox=dict(boxstyle="round,pad=0.4", fc="#f4f6f9",
                                    ec=FS.FAINT, lw=0.6))


def main():
    A = FD.load_analysis()
    fig = plt.figure(figsize=(11.0, 9.4))
    gs = fig.add_gridspec(2, 2, hspace=0.24, wspace=0.20,
                          left=0.055, right=0.965, top=0.93, bottom=0.06)
    axa = fig.add_subplot(gs[0, 0]); panel_a(axa, A); FS.panel_label(axa, "a")
    axb = fig.add_subplot(gs[0, 1]); panel_b(axb, A); FS.panel_label(axb, "b")
    axc = fig.add_subplot(gs[1, 0]); panel_c(axc, A); FS.panel_label(axc, "c")
    axd = fig.add_subplot(gs[1, 1]); panel_d(axd, A); FS.panel_label(axd, "d")
    fig.suptitle("Figure 3  |  Spectral connectivity and persistent-homology of "
                 "forced redistribution", x=0.055, ha="left",
                 fontsize=11, fontweight="bold")
    fig.savefig(C.FIGDIR / "figure3_connectivity_topology.png", bbox_inches="tight")
    fig.savefig(C.FIGDIR / "figure3_connectivity_topology.pdf", bbox_inches="tight")
    print("saved figure3")


if __name__ == "__main__":
    main()
