"""
Master analysis: consume SDM suitability surfaces and run the full geometric
pipeline (optimal transport -> connectivity -> topology -> coexistence risk),
with independent validation. Saves results/analysis.npz and results/summary.json.
"""
from __future__ import annotations
import json
import numpy as np
import config as C
import transport as OT
import connectivity as CN
import topology as TP
import risk as RK
from build_covariates import lonlat_to_rc
import pandas as pd


def main():
    S = np.load(C.RESULTS / "sdm.npz", allow_pickle=True)
    mask = S["mask"]; H = S["H"]; nx = int(S["nx"]); ny = int(S["ny"])
    lons = S["lons"]; lats = S["lats"]
    species = [sp for sp in C.SPECIES_NAMES if f"present__{sp}" in S.files]
    print("[analysis] species with SDMs:", species)

    store = {"mask": mask, "H": H, "lons": lons, "lats": lats,
             "nx": nx, "ny": ny}
    summary = {"scenario": C.SCENARIO_LABEL, "species": {}}

    pres_stack, fut_stack, fric_stack = [], [], []
    for sp in species:
        present = S[f"present__{sp}"]
        future = S[f"future__{sp}"]
        print(f"[OT] {sp} ...", flush=True)
        res = OT.analyze_pair(present, future, H, mask, lons, lats, cf=5)
        store[f"present__{sp}"] = present
        store[f"future__{sp}"] = future
        store[f"dlon__{sp}"] = res["dlon"].astype("float32")
        store[f"dlat__{sp}"] = res["dlat"].astype("float32")
        store[f"friction__{sp}"] = res["friction"].astype("float32")
        store[f"shift__{sp}"] = res["shift_km"].astype("float32")
        pres_stack.append(np.nan_to_num(present))
        fut_stack.append(np.nan_to_num(future))
        fric_stack.append(np.nan_to_num(res["friction"]))

        # ---- topology ----
        dp, fp = TP.analyze(present, mask)
        dfu, ff = TP.analyze(future, mask)
        store[f"pdiagP0__{sp}"] = dp[0]; store[f"pdiagP1__{sp}"] = dp[1]
        store[f"pdiagF0__{sp}"] = dfu[0]; store[f"pdiagF1__{sp}"] = dfu[1]
        wdist = TP.diagram_distance(dp, dfu, dim=0)

        # ---- validation 1: observed vs predicted shift ----
        obs = RK.observed_shift(sp)
        pred = RK.predicted_shift(res["dlon"], res["dlat"], present, mask)

        # ---- validation 2: interface ----
        occ = pd.read_csv(C.DATA_RAW / f"occ_{sp.replace(' ', '_')}.csv").dropna(
            subset=["lon", "lat"])
        rec = occ[occ.year >= 2015] if "year" in occ else occ
        r, c = lonlat_to_rc(rec.lon.values, rec.lat.values)
        inb = (r >= 0) & (r < ny) & (c >= 0) & (c < nx)
        occ_cells = np.unique(r[inb] * nx + c[inb])
        iv = RK.interface_validation(res["friction"], present, H, mask,
                                     occ_cells, nx)

        summary["species"][sp] = {
            "common": C.SPECIES_COMMON[sp],
            "W_shift_km": res["W_km"],
            "frag_present": fp, "frag_future": ff,
            "topo_change_W1": wdist,
            "observed_shift": None if obs is None else {
                "d_lon": obs["d_lon"], "d_lat": obs["d_lat"],
                "n_past": obs["n_past"], "n_recent": obs["n_recent"]},
            "predicted_shift": pred,
            "interface": iv,
        }
        print(f"    W={res['W_km']:.0f}km  frag {fp['n_patches']}->{ff['n_patches']}"
              f"  obs_dlat={None if obs is None else round(obs['d_lat'],3)}"
              f"  pred_dlat={pred['d_lat']:.3f}"
              f"  IV_auc={None if iv is None else round(iv['auc_friction'],3)}")

    # ---------------- community aggregates ----------------
    comm_p = np.mean(pres_stack, axis=0)
    comm_f = np.mean(fut_stack, axis=0)
    comm_p = np.where(mask, comm_p, np.nan)
    comm_f = np.where(mask, comm_f, np.nan)
    # weighted community friction
    wsum = np.sum(pres_stack, axis=0) + 1e-9
    comm_fric = np.sum([f * p for f, p in zip(fric_stack, pres_stack)], axis=0) / wsum
    comm_fric = np.where(mask, comm_fric, np.nan)

    print("[connectivity] community current ...", flush=True)
    R = CN.resistance_surface(comm_p, H, mask)
    cn = CN.solve_current(comm_p, comm_f, R, mask)
    pinch = CN.bottleneck_score(cn)

    print("[risk] Coexistence Risk Index ...", flush=True)
    cri, parts = RK.coexistence_risk(comm_fric, cn["current"], comm_p, comm_f,
                                     H, mask)

    store.update({
        "comm_present": comm_p.astype("float32"),
        "comm_future": comm_f.astype("float32"),
        "comm_friction": comm_fric.astype("float32"),
        "resistance": R.astype("float32"),
        "current": cn["current"].astype("float32"),
        "potential": cn["potential"].astype("float32"),
        "pinch": pinch.astype("float32"),
        "CRI": cri.astype("float32"),
        "cri_zf": parts["zf"].astype("float32"),
        "cri_zc": parts["zc"].astype("float32"),
        "cri_zg": parts["zg"].astype("float32"),
    })

    # community topology
    dpc, fpc = TP.analyze(comm_p, mask)
    dfc, ffc = TP.analyze(comm_f, mask)
    store["comm_pdiagP0"] = dpc[0]; store["comm_pdiagP1"] = dpc[1]
    store["comm_pdiagF0"] = dfc[0]; store["comm_pdiagF1"] = dfc[1]
    summary["community"] = {
        "frag_present": fpc, "frag_future": ffc,
        "topo_change_W1_H0": TP.diagram_distance(dpc, dfc, 0),
        "topo_change_W1_H1": TP.diagram_distance(dpc, dfc, 1),
        "mean_W_shift_km": float(np.nanmean(
            [summary["species"][sp]["W_shift_km"] for sp in species])),
    }

    # aggregate shift validation correlation
    obs_dlat = [summary["species"][sp]["observed_shift"]["d_lat"]
                for sp in species if summary["species"][sp]["observed_shift"]]
    pred_dlat = [summary["species"][sp]["predicted_shift"]["d_lat"]
                 for sp in species if summary["species"][sp]["observed_shift"]]
    if len(obs_dlat) >= 3:
        from scipy.stats import pearsonr, spearmanr
        summary["validation_shift"] = {
            "pearson": float(pearsonr(obs_dlat, pred_dlat)[0]),
            "spearman": float(spearmanr(obs_dlat, pred_dlat)[0]),
            "n": len(obs_dlat),
        }

    np.savez_compressed(C.RESULTS / "analysis.npz", **store)
    with open(C.RESULTS / "summary.json", "w") as fh:
        json.dump(summary, fh, indent=2, default=lambda o: float(o))
    print("[analysis] saved results/analysis.npz and summary.json")
    print(json.dumps(summary.get("validation_shift", {}), indent=2))


if __name__ == "__main__":
    main()
