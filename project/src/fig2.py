"""
Figure 2 — Entropic Displacement of habitat under climate change.
(a) Bivariate map of present vs future community suitability (loss/gain).
(b) Optimal-transport displacement field (streamlines colored by magnitude).
(c) Wasserstein range-shift vs latitude, per species (2D density + trends).
(d) Coexistence Friction hotspots with human-modification contours.
"""
from __future__ import annotations
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D
import config as C
import figstyle as FS
import figdata as FD

FS.apply()


def _bivariate_colors(x, y, n=4):
    """Map two [0,1] fields to a 2D color grid (present vs future)."""
    # blue = gain (future>present), red = loss, dark = high both
    import matplotlib.colors as mc
    c00 = np.array(mc.to_rgb("#f2f2ee"))   # low present, low future
    c10 = np.array(mc.to_rgb("#b2182b"))   # high present, low future (LOSS)
    c01 = np.array(mc.to_rgb("#2166ac"))   # low present, high future (GAIN)
    c11 = np.array(mc.to_rgb("#3b2f5e"))   # high both (stable core)
    xi = np.clip(x, 0, 1)[..., None]
    yi = np.clip(y, 0, 1)[..., None]
    col = (c00 * (1 - xi) * (1 - yi) + c10 * xi * (1 - yi)
           + c01 * (1 - xi) * yi + c11 * xi * yi)
    return np.clip(col, 0, 1)


def panel_a(ax, A):
    mask = A["mask"]; lons = A["lons"]; lats = A["lats"]
    p = A["comm_present"]; f = A["comm_future"]
    # normalize each to 0..1 by domain percentile
    def nrm(z):
        v = z[np.isfinite(z)]
        lo, hi = np.percentile(v, 2), np.percentile(v, 98)
        return np.clip((z - lo) / (hi - lo + 1e-9), 0, 1)
    rgb = _bivariate_colors(nrm(p), nrm(f))
    img = np.dstack([rgb, np.where(mask, 1.0, 0.0)])
    FS.sea(ax, mask, lons, lats)
    ax.imshow(img, extent=[lons[0], lons[-1], lats[-1], lats[0]], origin="upper",
              interpolation="nearest")
    FS.coastline_from_mask(ax, mask, lons, lats, lw=0.4)
    FS.map_axes(ax, lons, lats)
    ax.set_title("Present vs future habitat (SSP2-4.5)", loc="left")
    # inset 2D legend
    ins = ax.inset_axes([0.03, 0.62, 0.26, 0.30])
    gx, gy = np.meshgrid(np.linspace(0, 1, 40), np.linspace(0, 1, 40))
    ins.imshow(_bivariate_colors(gx, gy), origin="lower", extent=[0, 1, 0, 1])
    ins.set_xticks([]); ins.set_yticks([])
    ins.set_xlabel("present", fontsize=5.6, labelpad=1)
    ins.set_ylabel("future", fontsize=5.6, labelpad=1)
    ins.text(-0.05, 1.10, "gain", color="#2166ac", fontsize=5.6, fontweight="bold",
             transform=ins.transAxes)
    ins.text(1.02, -0.02, "loss", color="#b2182b", fontsize=5.6, fontweight="bold",
             transform=ins.transAxes, ha="left")
    for s in ins.spines.values():
        s.set_color(FS.FAINT); s.set_linewidth(0.5)


def panel_b(ax, A):
    mask = A["mask"]; lons = A["lons"]; lats = A["lats"]
    # community displacement = suitability-weighted mean over species
    sps = FD.species_present(A)
    w = np.zeros_like(mask, float); dl = np.zeros_like(mask, float); dp = np.zeros_like(mask, float)
    for sp in sps:
        pw = np.nan_to_num(A[f"present__{sp}"])
        dl += np.nan_to_num(A[f"dlon__{sp}"]) * pw
        dp += np.nan_to_num(A[f"dlat__{sp}"]) * pw
        w += pw
    w += 1e-9
    U = np.where(mask, dl / w, np.nan)
    V = np.where(mask, dp / w, np.nan)
    speed = np.hypot(U, V)
    FS.sea(ax, mask, lons, lats)
    im = FS.imshow_map(ax, np.where(mask, speed, np.nan), lons, lats, FS.EMBER,
                       vmax=np.nanpercentile(speed, 97))
    # streamlines on regular grid (matplotlib needs ascending y)
    Y = lats[::-1]
    Us = np.flipud(np.nan_to_num(U)); Vs = np.flipud(np.nan_to_num(V))
    spd = np.flipud(np.nan_to_num(speed))
    lw = 0.4 + 2.2 * (spd / (np.nanpercentile(speed, 97) + 1e-9))
    ax.streamplot(lons, Y, Us, Vs, density=1.6, color=FS.INK,
                  linewidth=np.clip(lw, 0.2, 2.0), arrowsize=0.5,
                  arrowstyle="-|>")
    FS.coastline_from_mask(ax, mask, lons, lats, lw=0.4)
    FS.map_axes(ax, lons, lats)
    FS.cbar(ax.figure, im, ax, "displacement (deg)")
    ax.set_title("Entropic displacement field  $T(x)-x$", loc="left")


def panel_c(ax, A):
    sps = FD.species_present(A)
    mask = A["mask"]; lats = A["lats"]
    LAT = np.meshgrid(A["lons"], lats)[1]
    # gather per-cell shift vs latitude across all species
    allx, ally = [], []
    for sp in sps:
        s = A[f"shift__{sp}"]
        p = A[f"present__{sp}"]
        ok = mask & np.isfinite(s) & (np.nan_to_num(p) > np.nanpercentile(p, 60))
        allx.append(LAT[ok]); ally.append(s[ok])
    X = np.concatenate(allx); Yv = np.concatenate(ally)
    hb = ax.hexbin(X, Yv, gridsize=34, bins="log", cmap=FS.SUIT, mincnt=1,
                   linewidths=0)
    # per-species latitudinal trend (median shift in lat bins)
    bins = np.linspace(lats[-1], lats[0], 12)
    ctr = 0.5 * (bins[1:] + bins[:-1])
    for sp in sps:
        s = A[f"shift__{sp}"]; p = A[f"present__{sp}"]
        ok = mask & np.isfinite(s) & (np.nan_to_num(p) > np.nanpercentile(p, 60))
        xx = LAT[ok]; yy = s[ok]
        med = []
        for i in range(len(bins) - 1):
            sel = (xx >= bins[i]) & (xx < bins[i + 1])
            med.append(np.median(yy[sel]) if sel.sum() > 20 else np.nan)
        med = np.array(med)
        ax.plot(ctr, med, color=C.SPECIES_COLOR[sp], lw=1.7, alpha=0.9,
                solid_capstyle="round")
        # redundant shape markers every few bins (colourblind backup)
        vis = np.isfinite(med)
        ax.plot(ctr[vis][::2], med[vis][::2], linestyle="none",
                marker=C.SPECIES_MARKER[sp], ms=4.5, mfc=C.SPECIES_COLOR[sp],
                mec="white", mew=0.5, alpha=0.95)
    FS.cbar(ax.figure, hb, ax, "cells (log)")
    ax.set_xlabel("Latitude (°N)")
    ax.set_ylabel("Required range shift (km)")
    ax.set_title("Poleward intensification of displacement", loc="left")
    # legend mapping each coloured trend line + shape marker to its species
    handles = [Line2D([0], [0], color=C.SPECIES_COLOR[sp], lw=1.7,
                      marker=C.SPECIES_MARKER[sp], ms=4.5, mfc=C.SPECIES_COLOR[sp],
                      mec="white", mew=0.5, label=C.SPECIES_COMMON[sp])
               for sp in sps]
    leg = ax.legend(handles=handles, loc="upper right", ncol=2, fontsize=5.7,
                    handlelength=1.5, columnspacing=0.9, labelspacing=0.3,
                    borderpad=0.4, framealpha=0.9, edgecolor=FS.FAINT)
    leg.get_frame().set_linewidth(0.5)


def panel_d(ax, A):
    mask = A["mask"]; lons = A["lons"]; lats = A["lats"]
    F = A["comm_friction"]; H = A["H"]
    FS.sea(ax, mask, lons, lats)
    Fp = np.where(mask, F, np.nan)
    im = FS.imshow_map(ax, Fp, lons, lats, FS.EMBER,
                       vmax=np.nanpercentile(Fp, 98))
    # human-modification contours
    Hs = np.where(mask, H, np.nan)
    ax.contour(np.flipud(np.nan_to_num(Hs)), levels=[0.4, 0.6, 0.8],
               colors=["#3b3b3b"], linewidths=[0.3, 0.45, 0.6],
               extent=[lons[0], lons[-1], lats[-1], lats[0]], origin="lower",
               alpha=0.5)
    FS.coastline_from_mask(ax, mask, lons, lats, lw=0.4)
    FS.map_axes(ax, lons, lats)
    FS.cbar(ax.figure, im, ax, r"friction $\langle T,\nabla H\rangle_+$")
    ax.set_title("Coexistence friction (habitat pushed toward people)", loc="left")


def main():
    A = FD.load_analysis()
    fig = plt.figure(figsize=(11.0, 9.4))
    gs = fig.add_gridspec(2, 2, hspace=0.24, wspace=0.18,
                          left=0.05, right=0.965, top=0.93, bottom=0.06)
    axa = fig.add_subplot(gs[0, 0]); panel_a(axa, A); FS.panel_label(axa, "a")
    axb = fig.add_subplot(gs[0, 1]); panel_b(axb, A); FS.panel_label(axb, "b")
    axc = fig.add_subplot(gs[1, 0]); panel_c(axc, A); FS.panel_label(axc, "c")
    axd = fig.add_subplot(gs[1, 1]); panel_d(axd, A); FS.panel_label(axd, "d")
    fig.suptitle("Figure 2  |  Optimal-transport geometry of climate-forced "
                 "range redistribution", x=0.05, ha="left",
                 fontsize=11, fontweight="bold")
    fig.savefig(C.FIGDIR / "figure2_transport.png", bbox_inches="tight")
    fig.savefig(C.FIGDIR / "figure2_transport.pdf", bbox_inches="tight")
    print("saved figure2")


if __name__ == "__main__":
    main()
