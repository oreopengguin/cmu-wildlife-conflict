"""
Figure SDM — present vs 2090 species distributions (one map per species).

Each panel: present habitat suitability (filled), the 2090 core-range boundary
(dashed contour) on top, and a mean-displacement arrow. The gap between the
bright present core and the dashed 2090 outline *is* the climate-forced shift.
Static companion to the interactive web map viewer.
"""
from __future__ import annotations
import json
import numpy as np
import matplotlib.pyplot as plt
import config as C
import figstyle as FS
import figdata as FD

FS.apply()
CORE = 0.5  # suitability level defining a species' "core range"


def species_panel(ax, A, sp, summ):
    mask = A["mask"]; lons = A["lons"]; lats = A["lats"]
    present = A[f"present__{sp}"]; future = A[f"future__{sp}"]
    # per-species contrast stretch (relative suitability) so habitat is visible;
    # future scaled by the SAME factor so the shift stays comparable.
    scale98 = np.nanpercentile(present[mask], 98) + 1e-9
    pN = np.clip(present / scale98, 0, 1)
    fN = np.clip(future / scale98, 0, 1)
    FS.sea(ax, mask, lons, lats)
    im = FS.imshow_map(ax, np.where(mask, pN, np.nan), lons, lats,
                       FS.SUIT, vmin=0, vmax=1)
    ext = [lons[0], lons[-1], lats[-1], lats[0]]
    # present core (thin solid) and 2090 core (dashed, species colour)
    ax.contour(np.flipud(np.nan_to_num(pN)), levels=[CORE], colors=["white"],
               linewidths=0.8, extent=ext, origin="lower", alpha=0.9)
    ax.contour(np.flipud(np.nan_to_num(fN)), levels=[CORE],
               colors=[C.SPECIES_COLOR[sp]], linewidths=1.8, linestyles="--",
               extent=ext, origin="lower")
    FS.coastline_from_mask(ax, mask, lons, lats, lw=0.35)
    FS.map_axes(ax, lons, lats)
    # mean displacement arrow (present-suitability-weighted), from summary
    pr = summ["species"][sp]["predicted_shift"]
    w = np.where(mask, np.clip(present, 0, None), 0.0); W = w.sum() + 1e-9
    LON, LAT = np.meshgrid(lons, lats)
    cx = float(np.sum(w * LON) / W); cy = float(np.sum(w * LAT) / W)
    scale = 6.0
    ax.annotate("", xy=(cx + pr["d_lon"] * scale, cy + pr["d_lat"] * scale),
                xytext=(cx, cy),
                arrowprops=dict(arrowstyle="-|>", color="white", lw=2.2,
                                mutation_scale=13))
    ax.annotate("", xy=(cx + pr["d_lon"] * scale, cy + pr["d_lat"] * scale),
                xytext=(cx, cy),
                arrowprops=dict(arrowstyle="-|>", color=C.SPECIES_COLOR[sp],
                                lw=1.3, mutation_scale=11))
    ax.set_title(f"{C.SPECIES_COMMON[sp]}", loc="left", fontsize=9)
    ax.text(0.04, 0.06, f"shift {summ['species'][sp]['W_shift_km']:.0f} km N",
            transform=ax.transAxes, fontsize=7, color="white", fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.28", fc=(0.05, 0.08, 0.15, 0.72),
                      ec="none"))
    return im


def legend_panel(ax, im):
    ax.axis("off")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.text(0.0, 0.92, "How to read", fontsize=10, fontweight="bold",
            family=FS.mpl.rcParams["font.family"])
    items = [
        ("filled colour", "present habitat suitability (per-species stretch)"),
        ("white outline", "present core range"),
        ("dashed outline", "2090 core range (SSP2-4.5)"),
        ("arrow", "mean poleward displacement"),
    ]
    y = 0.75
    for k, v in items:
        ax.text(0.02, y, f"• {k}:", fontsize=8, fontweight="bold", color=FS.INK)
        ax.text(0.40, y, v, fontsize=8, color=FS.MUTE)
        y -= 0.13
    # colourbar
    cax = ax.inset_axes([0.05, 0.06, 0.6, 0.06])
    cb = ax.figure.colorbar(im, cax=cax, orientation="horizontal")
    cb.set_label("relative suitability", fontsize=7.5)
    cb.ax.tick_params(labelsize=6.5)
    ax.text(0.0, 0.24, "The gap between the bright core and the dashed line\n"
            "is the habitat the climate forces each species to vacate.",
            fontsize=7.6, color=FS.INK, style="italic")


def main():
    A = FD.load_analysis()
    summ = FD.load_summary()
    sps = FD.species_present(A)
    fig = plt.figure(figsize=(12.6, 6.6))
    gs = fig.add_gridspec(2, 4, hspace=0.22, wspace=0.08,
                          left=0.02, right=0.98, top=0.9, bottom=0.03)
    im = None
    for i, sp in enumerate(sps):
        ax = fig.add_subplot(gs[i // 4, i % 4])
        im = species_panel(ax, A, sp, summ)
    legend_panel(fig.add_subplot(gs[1, 3]), im)
    fig.suptitle("Present vs 2090 species distributions  —  habitat suitability "
                 "and its climate-forced retreat (SSP2-4.5)",
                 x=0.02, ha="left", fontsize=12, fontweight="bold")
    fig.savefig(C.FIGDIR / "figureSDM_present_future.png", bbox_inches="tight")
    fig.savefig(C.FIGDIR / "figureSDM_present_future.pdf", bbox_inches="tight")
    print("saved figureSDM")


if __name__ == "__main__":
    main()
