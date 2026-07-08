"""
Spectral / circuit-theory connectivity of the climate-forced movement demand.

We route the *demand for movement* implied by climate-driven suitability change
through the real landscape resistance, using electrical-circuit theory
(McRae et al. 2008) implemented from scratch with a sparse graph Laplacian.

Physical picture:
  * Resistance R(x) rises with unsuitability and human modification.
  * Source/sink demand b(x) = present_suit - future_suit  (habitat LOST is a
    current source; habitat GAINED is a sink) -> the same mass the optimal-
    transport map must move, now constrained to flow through the landscape.
  * Solve the Poisson equation  L phi = b  on the weighted grid graph; edge
    currents  I_ij = c_ij (phi_i - phi_j)  give the movement field.
  * Node current density = corridor intensity; high current in high-H cells =
    conflict corridors / pinch-points.
"""
from __future__ import annotations
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla


def resistance_surface(suit, H, mask, alpha=4.0, gamma=3.0, base=0.05):
    """R = base + alpha*(1-suit) + gamma*H, on land; inf off-land."""
    R = base + alpha * (1.0 - np.clip(suit, 0, 1)) + gamma * np.clip(H, 0, 1)
    R = np.where(mask, R, np.nan)
    return R


def build_graph(R, mask):
    """4-neighbour weighted graph over land cells. Conductance = harmonic mean
    of neighbour conductances (1/R). Returns L (sparse), index maps."""
    ny, nx = R.shape
    idx = -np.ones((ny, nx), dtype=int)
    land = np.argwhere(mask)
    for k, (r, c) in enumerate(land):
        idx[r, c] = k
    n = len(land)
    rows, cols, vals = [], [], []
    Rf = R
    for (r, c) in land:
        i = idx[r, c]
        for dr, dc in ((0, 1), (1, 0)):
            rr, cc = r + dr, c + dc
            if rr < ny and cc < nx and mask[rr, cc]:
                j = idx[rr, cc]
                cond = 2.0 / (Rf[r, c] + Rf[rr, cc])   # harmonic-mean conductance
                rows += [i, j]; cols += [j, i]; vals += [cond, cond]
    W = sp.csr_matrix((vals, (rows, cols)), shape=(n, n))
    d = np.asarray(W.sum(axis=1)).ravel()
    L = sp.diags(d) - W
    return L, W, idx, land, d


def solve_current(suit_present, suit_future, R, mask):
    """Return node current-density field (corridor intensity) and edge stats."""
    L, W, idx, land, deg = build_graph(R, mask)
    n = len(land)
    b = np.zeros(n)
    demand = (suit_present - suit_future)          # + where habitat lost
    for k, (r, c) in enumerate(land):
        b[k] = demand[r, c]
    b -= b.mean()                                   # enforce zero-sum (solvable)
    # regularize the singular Laplacian (grounded solve)
    A = (L + 1e-8 * sp.identity(n)).tocsc()
    phi = spla.spsolve(A, b)
    phi -= phi.mean()

    # edge currents -> node current density
    node_curr = np.zeros(n)
    Wcoo = W.tocoo()
    for i, j, c in zip(Wcoo.row, Wcoo.col, Wcoo.data):
        if i < j:
            I = c * abs(phi[i] - phi[j])
            node_curr[i] += I
            node_curr[j] += I
    node_curr *= 0.5

    curr_grid = np.full(mask.shape, np.nan)
    phi_grid = np.full(mask.shape, np.nan)
    for k, (r, c) in enumerate(land):
        curr_grid[r, c] = node_curr[k]
        phi_grid[r, c] = phi[k]
    return dict(current=curr_grid, potential=phi_grid, idx=idx, land=land,
                node_current=node_curr, phi=phi, L=L, W=W)


def effective_resistance(L, i, j, n):
    """Effective resistance between two nodes via a grounded linear solve."""
    b = np.zeros(n); b[i] = 1.0; b[j] = -1.0; b -= b.mean()
    A = (L + 1e-8 * sp.identity(n)).tocsc()
    v = spla.spsolve(A, b)
    return float(v[i] - v[j])


def bottleneck_score(res):
    """Pinch-point score: cells whose removal would most raise resistance are
    approximated by high current density relative to local mean (flow squeeze)."""
    from scipy.ndimage import uniform_filter
    curr = np.nan_to_num(res["current"], nan=0.0)
    local = uniform_filter(curr, size=9) + 1e-9
    pinch = curr / local * (curr > np.nanpercentile(curr[curr > 0], 60))
    pinch[np.isnan(res["current"])] = np.nan
    return pinch
