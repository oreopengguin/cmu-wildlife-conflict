"""
Figure S1 — Robustness & solver verification.
(a) Range-shift under SSP2-4.5 vs SSP5-8.5 (dumbbell per species).
(b) Coexistence-friction spatial pattern is scenario-invariant (r=0.98).
(c) Wasserstein shift vs entropic-reg and vs grid coarsening (stability).
(d) The MaxEnt/PPP solver satisfies its defining constraint (feature-matching).
"""
from __future__ import annotations
import json
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import pearsonr
import config as C
import figstyle as FS

FS.apply()


def main():
    R = np.load(C.RESULTS / "robustness.npz", allow_pickle=True)
    J = json.load(open(C.RESULTS / "robustness.json"))
    fig = plt.figure(figsize=(11.0, 8.6))
    gs = fig.add_gridspec(2, 2, hspace=0.32, wspace=0.24,
                          left=0.08, right=0.95, top=0.9, bottom=0.09)

    # (a) dumbbell
    ax = fig.add_subplot(gs[0, 0]); FS.panel_label(ax, "a")
    sp = J["scenario"]["species"]
    w2 = [J["scenario"]["W245"][s] for s in sp]
    w5 = [J["scenario"]["W585"][s] for s in sp]
    order = np.argsort(w2)
    yy = np.arange(len(sp))
    for i, o in enumerate(order):
        ax.plot([w2[o], w5[o]], [i, i], color=FS.FAINT, lw=2, zorder=1)
        ax.scatter(w2[o], i, color="#1f7a7a", s=42, zorder=2)
        ax.scatter(w5[o], i, color="#c85a2b", s=42, zorder=2)
    ax.set_yticks(yy)
    ax.set_yticklabels([C.SPECIES_COMMON[sp[o]] for o in order], fontsize=7.2)
    ax.scatter([], [], color="#1f7a7a", label="SSP2-4.5")
    ax.scatter([], [], color="#c85a2b", label="SSP5-8.5")
    ax.legend(loc="lower right", fontsize=7)
    ax.set_xlabel("Wasserstein range shift (km)")
    ax.set_title("Range shift scales with emissions", loc="left")
    ax.tick_params(axis="y", length=0); ax.spines["left"].set_visible(False)

    # (b) friction scatter between scenarios
    ax = fig.add_subplot(gs[0, 1]); FS.panel_label(ax, "b")
    F2 = R["F2"]; F5 = R["F5"]; mask = R["mask"]
    m = mask & np.isfinite(F2) & np.isfinite(F5) & (F2 + F5 > 0)
    x = F2[m]; y = F5[m]
    hb = ax.hexbin(x, y, gridsize=42, bins="log", cmap=FS.EMBER, mincnt=1, linewidths=0)
    lim = [0, np.percentile(np.concatenate([x, y]), 99.5)]
    ax.plot(lim, lim, color=FS.INK, lw=0.9, ls="--")
    r = pearsonr(x, y)[0]
    ax.text(0.04, 0.95, f"Pearson r = {r:.2f}", transform=ax.transAxes, va="top",
            fontsize=8, bbox=dict(boxstyle="round,pad=0.3", fc="#fff4f0",
                                  ec=FS.FAINT, lw=0.6))
    ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_xlabel("friction — SSP2-4.5"); ax.set_ylabel("friction — SSP5-8.5")
    ax.set_title("Conflict pattern is scenario-invariant", loc="left")
    FS.cbar(fig, hb, ax, "cells (log)")

    # (c) reg + coarsening sensitivity
    ax = fig.add_subplot(gs[1, 0]); FS.panel_label(ax, "c")
    ax.plot(R["regs"], R["Wreg"], "-o", color="#8c2d62", ms=5, label="vs reg ε")
    ax.set_xlabel("entropic regularization  ε")
    ax.set_ylabel("Wasserstein shift (km)")
    ax.set_title("OT shift stable across settings", loc="left")
    ax.text(0.5, 0.06, f"reg CV = {J['reg_sensitivity']['cv']*100:.0f}%   ·   "
            f"grid CV = {J['coarsen_sensitivity']['cv']*100:.1f}%",
            transform=ax.transAxes, fontsize=7, color=FS.MUTE, ha="center")
    ins = ax.inset_axes([0.58, 0.5, 0.38, 0.42])
    ins.plot(R["cfs"], R["Wcf"], "-s", color="#2a6f97", ms=4)
    ins.set_title("vs grid coarsening", fontsize=6.5)
    ins.set_xlabel("factor", fontsize=6); ins.set_ylabel("km", fontsize=6)
    ins.tick_params(labelsize=6)
    for s in ins.spines.values():
        s.set_color(FS.FAINT)

    # (d) MaxEnt constraint verification
    ax = fig.add_subplot(gs[1, 1]); FS.panel_label(ax, "d")
    emp = R["emp"]; exp = R["exp"]
    ax.scatter(emp, exp, s=55, color="#1f7a7a", edgecolor=FS.INK, linewidth=0.5, zorder=3)
    lim = [min(emp.min(), exp.min()) - 0.1, max(emp.max(), exp.max()) + 0.1]
    ax.plot(lim, lim, color=FS.MUTE, lw=0.9, ls="--")
    r = J["maxent_constraint"]["pearson"]
    ax.text(0.04, 0.95, f"Pearson r = {r:.5f}\nRMSE = {J['maxent_constraint']['rmse']:.4f}",
            transform=ax.transAxes, va="top", fontsize=8,
            bbox=dict(boxstyle="round,pad=0.3", fc="#eefaf7", ec=FS.FAINT, lw=0.6))
    ax.set_xlim(lim); ax.set_ylim(lim); ax.set_aspect("equal")
    ax.set_xlabel("empirical feature mean at presences")
    ax.set_ylabel("model (Gibbs) expectation")
    ax.set_title("Solver satisfies the max-entropy constraint", loc="left")

    fig.suptitle("Figure S1  |  Robustness, scenario sensitivity, and solver "
                 "verification", x=0.08, ha="left", fontsize=11, fontweight="bold")
    fig.savefig(C.FIGDIR / "figureS1_robustness.png", bbox_inches="tight")
    fig.savefig(C.FIGDIR / "figureS1_robustness.pdf", bbox_inches="tight")
    print("saved figS1")


if __name__ == "__main__":
    main()
