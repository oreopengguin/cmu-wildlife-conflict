"""
Persistent homology of habitat-suitability surfaces (cubical complex).

Habitat fragmentation is a topological phenomenon: as we lower a suitability
threshold, habitat *patches* (H0 connected components) appear and merge, and
enclosed unsuitable *gaps* (H1 loops) are born and filled. Persistent homology
(Edelsbrunner & Harer 2010) quantifies this shape across all thresholds at once,
with a stability guarantee w.r.t. noise.

We compute superlevel-set persistence of suitability (feed -suitability to a
sublevel cubical complex), derive a persistence-based fragmentation index, and
measure structural range change present->future via bottleneck / Wasserstein
distance between diagrams.
"""
from __future__ import annotations
import numpy as np
import gudhi
from gudhi.wasserstein import wasserstein_distance as gudhi_wass


def _superlevel_diagram(suit, mask):
    """Persistence diagram of superlevel sets of suitability in [0,1].
    Returns dict with H0 and H1 arrays of (birth, death) in suitability units."""
    s = np.where(mask & np.isfinite(suit), np.clip(suit, 0, 1), 0.0)
    cc = gudhi.CubicalComplex(top_dimensional_cells=(-s))  # sublevel of -s
    cc.persistence(homology_coeff_field=2, min_persistence=0.0)
    out = {0: [], 1: []}
    for dim, (b, d) in cc.persistence():
        if dim in (0, 1):
            # convert from -s filtration back to suitability (birth>death)
            bb = -b
            dd = -d if np.isfinite(d) else 0.0
            out[dim].append((bb, dd))
    for k in out:
        out[k] = np.array(out[k]) if out[k] else np.zeros((0, 2))
    return out


def fragmentation_index(diag, tau=0.05):
    """Number of persistent habitat components (H0) with persistence > tau, and
    total persistence (sum of birth-death gaps). Higher = more fragmented."""
    h0 = diag[0]
    if len(h0) == 0:
        return dict(n_patches=0, total_persistence=0.0, mean_persistence=0.0)
    pers = np.abs(h0[:, 0] - h0[:, 1])
    keep = pers > tau
    return dict(
        n_patches=int(keep.sum()),
        total_persistence=float(pers.sum()),
        mean_persistence=float(pers[keep].mean()) if keep.any() else 0.0,
        n_loops=int(len(diag[1])),
    )


def diagram_distance(diag_a, diag_b, dim=0, order=1.0):
    """Wasserstein distance between two persistence diagrams (finite pts).
    Uses gudhi's optimal-transport diagram metric."""
    a = diag_a[dim]; b = diag_b[dim]
    # gudhi expects (birth, death) with birth<death; our superlevel has birth>death
    a2 = np.column_stack([np.minimum(a[:, 0], a[:, 1]), np.maximum(a[:, 0], a[:, 1])]) if len(a) else np.zeros((0, 2))
    b2 = np.column_stack([np.minimum(b[:, 0], b[:, 1]), np.maximum(b[:, 0], b[:, 1])]) if len(b) else np.zeros((0, 2))
    return float(gudhi_wass(a2, b2, order=order, internal_p=2.0))


def persistence_landscape(diag, dim=0, n_layers=5, n_x=200, xmin=0.0, xmax=1.0):
    """Compute persistence landscape functions (Bubenik 2015) for plotting."""
    pts = diag[dim]
    xs = np.linspace(xmin, xmax, n_x)
    if len(pts) == 0:
        return xs, np.zeros((n_layers, n_x))
    b = np.minimum(pts[:, 0], pts[:, 1])
    d = np.maximum(pts[:, 0], pts[:, 1])
    tent = np.zeros((len(pts), n_x))
    for i in range(len(pts)):
        tent[i] = np.maximum(0.0, np.minimum(xs - b[i], d[i] - xs))
    lam = np.sort(tent, axis=0)[::-1]
    L = lam[:n_layers] if len(lam) >= n_layers else np.vstack(
        [lam, np.zeros((n_layers - len(lam), n_x))])
    return xs, L


def analyze(suit, mask):
    diag = _superlevel_diagram(suit, mask)
    frag = fragmentation_index(diag)
    return diag, frag
