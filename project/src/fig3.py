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


def panel_c(fig, cell, A):
    """Persistence diagram as a joint plot: main scatter (colour = epoch, shape =
    homology dimension) with birth/death marginal-density strips ("heat maps in
    sections around the graph") and the legend tucked in the clear top corner."""
    from matplotlib.lines import Line2D
    from scipy.stats import gaussian_kde

    def bd(d, minpers=0.008):
        if len(d) == 0:
            return np.zeros(0), np.zeros(0)
        b = np.maximum(d[:, 0], d[:, 1]); dd = np.minimum(d[:, 0], d[:, 1])
        keep = (b - dd) > minpers
        return b[keep], dd[keep]
    pP0b, pP0d = bd(A["comm_pdiagP0"]); pP1b, pP1d = bd(A["comm_pdiagP1"])
    fP0b, fP0d = bd(A["comm_pdiagF0"]); fP1b, fP1d = bd(A["comm_pdiagF1"])
    presb = np.concatenate([pP0b, pP1b]); presd = np.concatenate([pP0d, pP1d])
    futb = np.concatenate([fP0b, fP1b]); futd = np.concatenate([fP0d, fP1d])
    allv = np.concatenate([presb, presd, futb, futd])
    hi = np.percentile(allv, 99.5) if len(allv) else 0.25

    inner = cell.subgridspec(2, 2, width_ratios=[4, 1.15], height_ratios=[1.15, 4],
                             wspace=0.05, hspace=0.05)
    axm = fig.add_subplot(inner[1, 0])
    axt = fig.add_subplot(inner[0, 0], sharex=axm)
    axr = fig.add_subplot(inner[1, 1], sharey=axm)
    axl = fig.add_subplot(inner[0, 1]); axl.axis("off")

    axm.plot([0, hi], [0, hi], color=FS.FAINT, lw=0.9, ls="--", zorder=0)
    def sc(b, d, color, marker):
        axm.scatter(b, d, s=12, facecolor=FS.to_rgba(color, 0.28),
                    edgecolor=FS.to_rgba(color, 0.75), linewidth=0.4,
                    marker=marker, rasterized=True, zorder=2)
    sc(pP0b, pP0d, _BLUE, "o"); sc(pP1b, pP1d, _BLUE, "^")
    sc(fP0b, fP0d, _ORANGE, "o"); sc(fP1b, fP1d, _ORANGE, "^")
    axm.set_xlim(-0.006, hi * 1.03); axm.set_ylim(-0.006, hi * 1.03)
    axm.set_aspect("equal")
    axm.set_xlabel("birth — suitability at patch peak")
    axm.set_ylabel("death — suitability at merge")
    axm.text(0.035, 0.97, "features far below the diagonal\n= persistent habitat cores",
             transform=axm.transAxes, va="top", ha="left", fontsize=6, color=FS.MUTE)

    xs = np.linspace(0, hi, 220)
    def kde_fill(ax, data, color, vertical=False):
        if len(data) < 5:
            return
        dens = gaussian_kde(data)(xs)
        if vertical:
            ax.fill_betweenx(xs, 0, dens, color=color, alpha=0.20)
            ax.plot(dens, xs, color=color, lw=1.5)
        else:
            ax.fill_between(xs, 0, dens, color=color, alpha=0.20)
            ax.plot(xs, dens, color=color, lw=1.5)
    kde_fill(axt, presb, _BLUE); kde_fill(axt, futb, _ORANGE)
    kde_fill(axr, presd, _BLUE, vertical=True); kde_fill(axr, futd, _ORANGE, vertical=True)
    for a in (axt, axr):
        a.tick_params(labelbottom=False, labelleft=False, length=0)
        for s in a.spines.values():
            s.set_visible(False)
    axt.set_ylabel("birth\ndensity", fontsize=5.6, color=FS.MUTE, rotation=0,
                   ha="right", va="center", labelpad=2)
    axr.set_xlabel("death\ndensity", fontsize=5.6, color=FS.MUTE)

    handles = [Line2D([0], [0], marker="s", ls="none", mfc=_BLUE, mec="none", ms=8, label="present"),
               Line2D([0], [0], marker="s", ls="none", mfc=_ORANGE, mec="none", ms=8, label="future"),
               Line2D([0], [0], marker="o", ls="none", mfc="none", mec=FS.INK, ms=6, label="H$_0$ patches"),
               Line2D([0], [0], marker="^", ls="none", mfc="none", mec=FS.INK, ms=6, label="H$_1$ loops")]
    axl.legend(handles=handles, loc="center", fontsize=6.0, handlelength=1.0,
               handletextpad=0.4, labelspacing=0.55, borderpad=0.2, frameon=False)
    axt.set_title("Persistence diagram: shape of the range", loc="left", fontsize=9.5,
                  fontweight="bold")
    FS.panel_label(axt, "c")


def panel_d(ax, A):
    dP0 = {0: A["comm_pdiagP0"], 1: A["comm_pdiagP1"]}
    dF0 = {0: A["comm_pdiagF0"], 1: A["comm_pdiagF1"]}
    xs, LP = TP.persistence_landscape(dP0, dim=0, n_layers=4)
    _, LF = TP.persistence_landscape(dF0, dim=0, n_layers=4)
    # deeper layers first (light), then the bold primary envelope on top
    for i in range(1, LP.shape[0]):
        ax.plot(xs, LP[i], color=_BLUE, lw=1.0, alpha=0.32)
        ax.plot(xs, LF[i], color=_ORANGE, lw=1.0, alpha=0.32)
    ax.fill_between(xs, LP[0], color=_BLUE, alpha=0.11)
    ax.fill_between(xs, LF[0], color=_ORANGE, alpha=0.11)
    ax.plot(xs, LP[0], color=_BLUE, lw=2.8, label="present", solid_capstyle="round")
    ax.plot(xs, LF[0], color=_ORANGE, lw=2.8, label="future", solid_capstyle="round")
    ax.set_xlabel("suitability threshold")
    ax.set_ylabel(r"persistence landscape $\lambda_k$")
    ax.set_title("Topological simplification of habitat", loc="left")
    ax.legend(loc="upper right", fontsize=7.6, handlelength=1.4)
    ax.set_xlim(0, 0.32)
    s = FD.load_summary()["community"]
    fp = s["frag_present"]; ff = s["frag_future"]
    arw = r"$\rightarrow$"
    txt = (f"patches (H$_0$): {fp['n_patches']} {arw} {ff['n_patches']}\n"
           f"loops (H$_1$): {fp['n_loops']} {arw} {ff['n_loops']}\n"
           f"total persistence: {fp['total_persistence']:.2f} {arw} "
           f"{ff['total_persistence']:.2f}")
    ax.text(0.03, 0.86, txt, transform=ax.transAxes, va="top", fontsize=6.6,
            color=FS.INK, bbox=dict(boxstyle="round,pad=0.4", fc="#f4f6f9",
                                    ec=FS.FAINT, lw=0.6))


def main():
    A = FD.load_analysis()
    fig = plt.figure(figsize=(11.0, 9.4))
    gs = fig.add_gridspec(2, 2, hspace=0.24, wspace=0.20,
                          left=0.055, right=0.965, top=0.93, bottom=0.06)
    axa = fig.add_subplot(gs[0, 0]); panel_a(axa, A); FS.panel_label(axa, "a")
    axb = fig.add_subplot(gs[0, 1]); panel_b(axb, A); FS.panel_label(axb, "b")
    panel_c(fig, gs[1, 0], A)      # joint plot: builds its own sub-gridspec + "c" label
    axd = fig.add_subplot(gs[1, 1]); panel_d(axd, A); FS.panel_label(axd, "d")
    fig.suptitle("Figure 3  |  Spectral connectivity and persistent-homology of "
                 "forced redistribution", x=0.055, ha="left",
                 fontsize=11, fontweight="bold")
    fig.savefig(C.FIGDIR / "figure3_connectivity_topology.png", bbox_inches="tight")
    fig.savefig(C.FIGDIR / "figure3_connectivity_topology.pdf", bbox_inches="tight")
    print("saved figure3")


if __name__ == "__main__":
    main()
