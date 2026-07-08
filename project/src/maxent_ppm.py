"""
From-scratch Maximum-Entropy / Poisson-Point-Process species distribution model.

Theory (Renner & Warton 2013; Fithian & Hastie 2013; Phillips et al. 2006):
    The MaxEnt distribution is the Gibbs distribution p(x) ∝ exp(β·f(x)) that
    maximizes entropy subject to matching feature expectations at presences.
    Its fit is EXACTLY a regularized inhomogeneous Poisson point process: the
    log-intensity is linear in features, estimated by penalized Poisson
    likelihood on a quadrature grid (the Berman–Turner device).

We implement:
  * MaxEnt-style feature classes: linear, quadratic, product, and hinge
    features, with train-range CLAMPING for honest future projection.
  * An elastic-net penalized Poisson-PPP objective solved by FISTA
    (accelerated proximal gradient) with soft-thresholding + backtracking.
  * Spatial block cross-validation and presence-only skill metrics
    (AUC, Boyce continuous index, TSS at max-TSS threshold).

Everything is numpy; no ML framework. This is the mathematical heart.
"""
from __future__ import annotations
import numpy as np
from dataclasses import dataclass, field
import config as C


# ============================================================================
# Feature engineering (MaxEnt feature classes) with clamping
# ============================================================================
@dataclass
class FeatureMaker:
    n_pred: int
    knots: int = 4                      # hinge knots per predictor
    use_products: bool = True
    lo: np.ndarray = field(default=None) # per-predictor clamp range (train)
    hi: np.ndarray = field(default=None)
    hinge_kn: list = field(default=None)
    names: list = field(default=None)

    def fit(self, X):
        self.lo = np.percentile(X, 1, axis=0)
        self.hi = np.percentile(X, 99, axis=0)
        self.hinge_kn = []
        for j in range(self.n_pred):
            self.hinge_kn.append(np.linspace(self.lo[j], self.hi[j], self.knots + 2)[1:-1])
        self.names = self._build_names()
        return self

    def _build_names(self):
        names = [f"lin{j}" for j in range(self.n_pred)]
        names += [f"quad{j}" for j in range(self.n_pred)]
        if self.use_products:
            for a in range(self.n_pred):
                for b in range(a + 1, self.n_pred):
                    names.append(f"prod{a}x{b}")
        for j in range(self.n_pred):
            for k in range(self.knots):
                names.append(f"hf{j}_{k}")   # forward hinge
                names.append(f"hr{j}_{k}")   # reverse hinge
        return names

    def transform(self, X, clamp=True):
        X = np.asarray(X, dtype="float64")
        if clamp:
            X = np.clip(X, self.lo, self.hi)
        feats = [X, X ** 2]
        if self.use_products:
            prod = []
            for a in range(self.n_pred):
                for b in range(a + 1, self.n_pred):
                    prod.append(X[:, a] * X[:, b])
            feats.append(np.stack(prod, axis=1))
        hinges = []
        for j in range(self.n_pred):
            xj = X[:, j]
            for k in self.hinge_kn[j]:
                rng = (self.hi[j] - k) + 1e-9
                hinges.append(np.clip((xj - k) / rng, 0, 1))          # forward
                rng2 = (k - self.lo[j]) + 1e-9
                hinges.append(np.clip((k - xj) / rng2, 0, 1))         # reverse
        feats.append(np.stack(hinges, axis=1))
        M = np.concatenate(feats, axis=1)
        return M


def standardize_design(M, mu=None, sd=None):
    if mu is None:
        mu = M.mean(axis=0)
        sd = M.std(axis=0) + 1e-9
    return (M - mu) / sd, mu, sd


# ============================================================================
# Elastic-net Poisson Point Process, solved by FISTA
# ============================================================================
@dataclass
class MaxentPPM:
    l1: float = 1e-3          # L1 strength (sparsity / MaxEnt regularization)
    l2: float = 1e-3          # L2 strength (ridge / stability)
    max_iter: int = 800
    tol: float = 1e-7
    beta: np.ndarray = None
    b0: float = 0.0
    feat_mu: np.ndarray = None
    feat_sd: np.ndarray = None

    def _obj(self, eta, y, w):
        # weighted Poisson neg-loglik (Berman-Turner): sum w*(exp(eta) - y*eta)
        return np.sum(w * (np.exp(eta) - y * eta))

    def fit(self, M, y, w):
        """M: design (n,p); y: Berman-Turner response (presence/w at pres, 0 bg);
        w: quadrature weights."""
        Mz, self.feat_mu, self.feat_sd = standardize_design(M)
        n, p = Mz.shape
        W = w.sum()
        wt = w / W
        yb = y                      # response stays; weights carry area
        beta = np.zeros(p)
        b0 = np.log(max((yb * w).sum() / W, 1e-8))
        z = beta.copy(); zb = b0
        t = 1.0
        L = 1.0                     # Lipschitz estimate (backtracked)
        prev = np.inf

        # FISTA: gradient evaluated at the momentum point z
        ETA_CLIP = 30.0                      # guard exp() against overflow
        for it in range(self.max_iter):
            eta_z = np.clip(zb + Mz @ z, -ETA_CLIP, ETA_CLIP)
            lam = np.exp(eta_z)
            resid = wt * (lam - yb)
            g0 = resid.sum()
            g = Mz.T @ resid + self.l2 * z
            f_z = np.sum(wt * (lam - yb * eta_z)) + 0.5 * self.l2 * z @ z

            # backtracking on L
            while True:
                step = 1.0 / L
                b0_new = zb - step * g0
                b_prox = z - step * g
                # soft-threshold (L1 prox) on penalized coeffs (all beta, not b0)
                thr = self.l1 * step
                b_new = np.sign(b_prox) * np.maximum(np.abs(b_prox) - thr, 0.0)
                eta_new = np.clip(b0_new + Mz @ b_new, -ETA_CLIP, ETA_CLIP)
                lam_new = np.exp(eta_new)
                f_new = np.sum(wt * (lam_new - yb * eta_new)) + 0.5 * self.l2 * b_new @ b_new
                db0 = b0_new - zb
                db = b_new - z
                quad = f_z + g0 * db0 + g @ db + 0.5 * L * (db0 ** 2 + db @ db)
                if f_new <= quad + 1e-12 or L > 1e12:
                    break
                L *= 2.0
            # FISTA momentum
            t_new = 0.5 * (1 + np.sqrt(1 + 4 * t * t))
            mom = (t - 1) / t_new
            zb = b0_new + mom * (b0_new - b0)
            z = b_new + mom * (b_new - beta)
            b0, beta = b0_new, b_new
            t = t_new
            L = max(L * 0.7, 1e-3)   # allow L to decrease
            obj = f_new + self.l1 * np.abs(b_new).sum()
            if abs(prev - obj) < self.tol * (abs(prev) + 1e-12):
                break
            prev = obj
        self.beta, self.b0 = beta, b0
        self.n_iter_ = it + 1
        self.nnz_ = int(np.sum(np.abs(beta) > 1e-8))
        return self

    def log_intensity(self, M):
        Mz = (M - self.feat_mu) / self.feat_sd
        return np.clip(self.b0 + Mz @ self.beta, -30.0, 30.0)

    def suitability(self, M):
        """Cloglog probability of presence (MaxEnt-like 0..1 output)."""
        eta = self.log_intensity(M)
        eta = eta - eta.max()             # numerical stability of exp
        lam = np.exp(eta)
        return 1.0 - np.exp(-lam)


# ============================================================================
# Presence-only skill metrics
# ============================================================================
def auc_presence_background(score_pres, score_bg, n_pairs=200000, rng=None):
    rng = rng or np.random.default_rng(0)
    a = rng.choice(score_pres, size=n_pairs)
    b = rng.choice(score_bg, size=n_pairs)
    return float(np.mean((a > b) + 0.5 * (a == b)))


def boyce_index(score_pres, score_bg, n_bins=20, window=0.1):
    """Continuous Boyce index (Hirzel et al. 2006): Spearman corr of
    predicted-to-expected ratio across suitability classes."""
    from scipy.stats import spearmanr
    lo, hi = np.min(score_bg), np.max(score_bg)
    centers = np.linspace(lo, hi, n_bins)
    half = window * (hi - lo)
    F = []
    P = []
    for c in centers:
        m0, m1 = c - half, c + half
        pe = np.mean((score_pres >= m0) & (score_pres <= m1))
        ex = np.mean((score_bg >= m0) & (score_bg <= m1))
        if ex > 0:
            F.append(pe / ex)
            P.append(c)
    if len(F) < 3:
        return np.nan
    rho, _ = spearmanr(P, F)
    return float(rho)


def tss_max(score_pres, score_bg, n_thr=100):
    thr = np.linspace(min(score_pres.min(), score_bg.min()),
                      max(score_pres.max(), score_bg.max()), n_thr)
    best = -1
    for t in thr:
        tpr = np.mean(score_pres >= t)
        fpr = np.mean(score_bg >= t)
        tss = tpr - fpr
        if tss > best:
            best = tss
    return float(best)
