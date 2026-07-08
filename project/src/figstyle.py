"""
Shared figure aesthetics: a restrained, publication-grade matplotlib style with
perceptually-uniform colormaps, consistent typography, and helper primitives for
maps, panel labels, and scalebars. Designed for dense multi-panel figures.
"""
from __future__ import annotations
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, to_rgba
import config as C

# ----------------------------------------------------------------------------
# Global rcParams
# ----------------------------------------------------------------------------
INK = "#14161a"
MUTE = "#5b6470"
FAINT = "#c7ccd4"
PAPER = "#ffffff"

def apply():
    mpl.rcParams.update({
        "figure.dpi": 130,
        "savefig.dpi": 400,
        "figure.facecolor": PAPER,
        "axes.facecolor": PAPER,
        "savefig.facecolor": PAPER,
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
        "font.size": 8.5,
        "axes.titlesize": 9.5,
        "axes.titleweight": "bold",
        "axes.labelsize": 8.5,
        "axes.edgecolor": INK,
        "axes.linewidth": 0.8,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK,
        "ytick.color": INK,
        "xtick.labelsize": 7.5,
        "ytick.labelsize": 7.5,
        "xtick.direction": "out",
        "ytick.direction": "out",
        "xtick.major.size": 3.0,
        "ytick.major.size": 3.0,
        "xtick.major.width": 0.7,
        "ytick.major.width": 0.7,
        "legend.frameon": False,
        "legend.fontsize": 7.5,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": False,
        "lines.antialiased": True,
        "patch.linewidth": 0.5,
        "mathtext.fontset": "dejavusans",
    })

# ----------------------------------------------------------------------------
# Perceptually-uniform / bespoke colormaps
# ----------------------------------------------------------------------------
def _cmap(name, colors):
    return LinearSegmentedColormap.from_list(name, colors)

# suitability: deep navy -> teal -> gold -> warm white (like a refined "batlow")
SUIT = _cmap("suit", ["#0b1026", "#123a5e", "#1f7a7a", "#5fae57",
                      "#d9c14a", "#f6efc0"])
# friction / risk: cool -> hot ember
EMBER = _cmap("ember", ["#0d0a1f", "#3b1f5e", "#8c2d62", "#d64545",
                        "#f28c3b", "#ffe9a8"])
# current / flow: electric
FLOW = _cmap("flow", ["#04121f", "#0a3d62", "#1e88c9", "#57d0f0", "#e6faff"])
# divergent shift (loss<->gain)
DIVSHIFT = _cmap("divshift", ["#5e3c99", "#9db8d2", "#f7f7f7",
                              "#f4a582", "#b2182b"])
# human modification
HUMAN = _cmap("human", ["#f7f7f2", "#dfc27d", "#a6611a", "#5e2f0d"])

# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def panel_label(ax, text, dx=-0.02, dy=1.02, fs=12):
    ax.text(dx, dy, text, transform=ax.transAxes, fontsize=fs,
            fontweight="bold", va="bottom", ha="right", color=INK)


def map_axes(ax, lons, lats, grid=True):
    ax.set_xlim(lons[0], lons[-1])
    ax.set_ylim(lats[-1], lats[0])
    ax.set_aspect(1.0 / np.cos(np.radians(np.mean(lats))))
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(True); s.set_color(FAINT); s.set_linewidth(0.6)


def coastline_from_mask(ax, mask, lons, lats, color=INK, lw=0.35):
    """Draw a crude coastline as the boundary of the land mask via contour."""
    extent = [lons[0], lons[-1], lats[-1], lats[0]]
    ax.contour(np.flipud(mask.astype(float)), levels=[0.5], colors=[color],
               linewidths=lw, extent=extent, origin="lower")


def add_scalebar(ax, lons, lats, km=500, y_frac=0.06, x_frac=0.08):
    lat0 = np.mean(lats)
    deg = km / (111.0 * np.cos(np.radians(lat0)))
    x0 = lons[0] + (lons[-1] - lons[0]) * x_frac
    y0 = lats[-1] + (lats[0] - lats[-1]) * y_frac
    ax.plot([x0, x0 + deg], [y0, y0], color=INK, lw=2.2, solid_capstyle="butt")
    ax.text(x0 + deg / 2, y0 + (lats[0]-lats[-1])*0.012, f"{km} km",
            ha="center", va="bottom", fontsize=6.5, color=INK)


def imshow_map(ax, field, lons, lats, cmap, vmin=None, vmax=None, alpha=1.0):
    extent = [lons[0], lons[-1], lats[-1], lats[0]]
    return ax.imshow(field, extent=extent, origin="upper", cmap=cmap,
                     vmin=vmin, vmax=vmax, alpha=alpha, interpolation="nearest")


def cbar(fig, mappable, ax, label, fraction=0.046, pad=0.03):
    cb = fig.colorbar(mappable, ax=ax, fraction=fraction, pad=pad)
    cb.outline.set_linewidth(0.5)
    cb.outline.set_edgecolor(FAINT)
    cb.set_label(label, fontsize=7.2)
    cb.ax.tick_params(labelsize=6.5, width=0.6, length=2.2)
    return cb


def sea(ax, mask, lons, lats, color="#eef1f5"):
    extent = [lons[0], lons[-1], lats[-1], lats[0]]
    ax.imshow(np.where(mask, np.nan, 1.0), extent=extent, origin="upper",
              cmap=mpl.colors.ListedColormap([color]), interpolation="nearest")
