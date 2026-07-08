"""
Robustness / sensitivity analysis for the Supplement:
  (1) Scenario sensitivity: SSP2-4.5 vs SSP5-8.5 (Wasserstein shift & CRI).
  (2) Entropic-regularization sensitivity of the OT range-shift.
  (3) Grid-coarsening sensitivity of the OT range-shift.
  (4) Numerical verification that the MaxEnt/PPP fit matches feature
      expectations at presences (the defining maximum-entropy constraint).
Saves results/robustness.npz + robustness.json.
"""
from __future__ import annotations
import json
import numpy as np
import config as C
import transport as OT
import risk as RK
from maxent_ppm import FeatureMaker, MaxentPPM

RNG = np.random.default_rng(C.RANDOM_SEED)


def scenario_sensitivity(S):
    mask = S["mask"]; H = S["H"]; lons = S["lons"]; lats = S["lats"]
    species = [sp for sp in C.SPECIES_NAMES if f"present__{sp}" in S.files]
    W245, W585 = {}, {}
    fr245, fr585 = [], []
    pres = []
    for sp in species:
        p = S[f"present__{sp}"]; f2 = S[f"future__{sp}"]; f5 = S[f"future585__{sp}"]
        r2 = OT.analyze_pair(p, f2, H, mask, lons, lats, cf=5)
        r5 = OT.analyze_pair(p, f5, H, mask, lons, lats, cf=5)
        W245[sp] = r2["W_km"]; W585[sp] = r5["W_km"]
        fr245.append(np.nan_to_num(r2["friction"]))
        fr585.append(np.nan_to_num(r5["friction"]))
        pres.append(np.nan_to_num(p))
    wsum = np.sum(pres, axis=0) + 1e-9
    F2 = np.sum([a * b for a, b in zip(fr245, pres)], axis=0) / wsum
    F5 = np.sum([a * b for a, b in zip(fr585, pres)], axis=0) / wsum
    m = mask & np.isfinite(F2) & np.isfinite(F5)
    from scipy.stats import pearsonr
    r_fr = pearsonr(F2[m], F5[m])[0]
    return dict(species=species, W245=W245, W585=W585,
                friction_corr=float(r_fr),
                F2=np.where(mask, F2, np.nan), F5=np.where(mask, F5, np.nan))


def reg_sensitivity(S, sp="Ursus arctos"):
    mask = S["mask"]; H = S["H"]; lons = S["lons"]; lats = S["lats"]
    p = S[f"present__{sp}"]; f = S[f"future__{sp}"]
    regs = [0.008, 0.015, 0.02, 0.03, 0.05, 0.08]
    Ws = []
    for r in regs:
        Ws.append(OT.analyze_pair(p, f, H, mask, lons, lats, cf=5,
                                  reg_frac=r)["W_km"])
    return regs, Ws


def coarsen_sensitivity(S, sp="Ursus arctos"):
    mask = S["mask"]; H = S["H"]; lons = S["lons"]; lats = S["lats"]
    p = S[f"present__{sp}"]; f = S[f"future__{sp}"]
    cfs = [4, 5, 6, 7, 8]
    Ws = []
    for cf in cfs:
        Ws.append(OT.analyze_pair(p, f, H, mask, lons, lats, cf=cf)["W_km"])
    return cfs, Ws


def maxent_constraint_check():
    """Fit a model and verify empirical feature means at presences ~ model
    expectation under the fitted Gibbs distribution (MaxEnt's defining property)."""
    d = np.load(C.DATA_PROC / "dataset.npz", allow_pickle=True)
    Pz = d["Pz"]; nx = int(d["nx"]); bg = d["background"]
    sp = "Lynx lynx"
    pres = d[f"pres__{sp}"]

    def cov(cells):
        r = cells // nx; c = cells % nx
        return Pz[:, r, c].T
    fm = FeatureMaker(n_pred=Pz.shape[0], knots=4, use_products=True)
    Mbg = fm.fit(cov(bg)).transform(cov(bg))
    Mp = fm.transform(cov(pres))
    model = MaxentPPM(l1=1e-3, l2=1e-3, max_iter=800)
    M = np.vstack([Mp, Mbg])
    y = np.concatenate([np.ones(len(Mp)), np.zeros(len(Mbg))])
    w = np.concatenate([np.full(len(Mp), 1e-6), np.ones(len(Mbg))])
    model.fit(M, y / w, w)
    # empirical feature means at presence
    emp = Mp.mean(axis=0)
    # model expectation: weight background by fitted Gibbs density
    eta = model.log_intensity(Mbg)
    p = np.exp(eta - eta.max()); p /= p.sum()
    exp = (Mbg * p[:, None]).sum(axis=0)
    # compare on the first (linear) features
    k = Pz.shape[0]
    from scipy.stats import pearsonr
    r = pearsonr(emp[:k], exp[:k])[0]
    rmse = float(np.sqrt(np.mean((emp[:k] - exp[:k]) ** 2)))
    return dict(emp=emp[:k].tolist(), exp=exp[:k].tolist(),
                pearson=float(r), rmse=rmse, nnz=int(model.nnz_))


def main():
    S = np.load(C.RESULTS / "sdm.npz", allow_pickle=True)
    print("[robust] scenario sensitivity ...", flush=True)
    scen = scenario_sensitivity(S)
    print("[robust] reg sensitivity ...", flush=True)
    regs, Wreg = reg_sensitivity(S)
    print("[robust] coarsening sensitivity ...", flush=True)
    cfs, Wcf = coarsen_sensitivity(S)
    print("[robust] MaxEnt constraint check ...", flush=True)
    mx = maxent_constraint_check()

    np.savez_compressed(
        C.RESULTS / "robustness.npz",
        F2=scen["F2"], F5=scen["F5"], mask=S["mask"],
        lons=S["lons"], lats=S["lats"],
        regs=np.array(regs), Wreg=np.array(Wreg),
        cfs=np.array(cfs), Wcf=np.array(Wcf),
        emp=np.array(mx["emp"]), exp=np.array(mx["exp"]),
    )
    out = {
        "scenario": {
            "species": scen["species"],
            "W245": scen["W245"], "W585": scen["W585"],
            "friction_corr_245_585": scen["friction_corr"],
        },
        "reg_sensitivity": {"regs": regs, "W_km": Wreg,
                            "cv": float(np.std(Wreg) / np.mean(Wreg))},
        "coarsen_sensitivity": {"cfs": cfs, "W_km": Wcf,
                                "cv": float(np.std(Wcf) / np.mean(Wcf))},
        "maxent_constraint": {"pearson": mx["pearson"], "rmse": mx["rmse"],
                              "nnz": mx["nnz"]},
    }
    with open(C.RESULTS / "robustness.json", "w") as fh:
        json.dump(out, fh, indent=2)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
