# The Geometry of Coexistence

**Predicting emergent human–wildlife conflict from the geometry of climate-forced
species redistribution** — using optimal transport, spectral graph theory, and
persistent homology on a from-scratch maximum-entropy species distribution model.

CMU Pre-College Computational Biology — Final Project, **Topic 25** (*How can we
model the ways that wildlife interact with humans and human-made communities?*).
Foundational reference: Phillips, Anderson & Schapire (2006), MaxEnt.

---

## The one-sentence idea

> Conflict emerges where climate forces a species' suitable habitat to move into
> human-dominated space and the landscape can't route the animals around it — and
> we can predict *where*, **without ever training on conflict data**.

## What's here

```
project/
├── docs/
│   ├── 01_literature_review.md        50+ annotated references (5 threads)
│   ├── 02_research_plan.md             full methodology & novelty
│   └── ONE_PAGER_for_teammates.md      plain-English explainer (no jargon)
├── src/                               reproducible pipeline (numpy-first)
│   ├── config.py  io_utils.py         study domain, grid, raster IO
│   ├── download_gbif.py download_hist.py   GBIF occurrences (recent + historical)
│   ├── build_covariates.py            climate/human stacks, thinning, TG-background
│   ├── maxent_ppm.py  run_sdm.py      FROM-SCRATCH elastic-net MaxEnt/PPP + FISTA
│   ├── transport.py                   entropic optimal transport (Sinkhorn) + friction
│   ├── connectivity.py                spectral circuit-theory corridors
│   ├── topology.py                    cubical persistent homology (GUDHI)
│   ├── risk.py  analysis.py           Coexistence Risk Index + validation
│   ├── robustness.py                  scenario/reg/grid sensitivity + solver check
│   ├── figstyle.py fig1-4.py figS1.py publication figures
│   └── build_site.py                  self-contained website
├── figures/                           figure{1-4}.png/pdf + figureS1 + web/
├── results/                           sdm.npz, analysis.npz, *.json
├── manuscript/manuscript.md           full Nature-style manuscript
├── website/index.html                 self-contained interactive site
└── run_pipeline.sh                    end-to-end runner
```

## Data (all open, no institutional login)

- **GBIF** occurrence records (public API) — 7 conflict-prone European mammals,
  recent (2015–2026) + historical (1990–2009) epochs.
- **WorldClim 2.1** bioclim — present + SSP2-4.5 & SSP5-8.5 futures (2081–2100).
- **Global Human Modification** (Kennedy et al. 2019, figshare) — human pressure H(x).

## Reproduce

```bash
python3 -m venv .venv
.venv/bin/pip install numpy==1.26.4 scipy pandas matplotlib scikit-learn \
    networkx POT ripser persim rasterio pyproj gudhi pillow
# 1. download data (cached in data/raw)
cd src
../.venv/bin/python download_gbif.py      # recent occurrences
../.venv/bin/python download_hist.py      # historical occurrences
#   climate + gHM are fetched with curl (see docs/02_research_plan.md)
# 2. run everything
cd .. && ./run_pipeline.sh
```

## Headline results

| Result | Value |
|---|---|
| SDM spatial-CV AUC (7 species) | 0.76 – 0.92 (mean 0.84) |
| Mean climate-forced range shift (SSP2-4.5) | 484 km (poleward, all 7 taxa) |
| Predicted vs observed shift | Spearman ρ = 0.64 (n = 7) |
| Friction → realized interface | permutation p = 0.0005 |
| Conflict pattern SSP2-4.5 vs SSP5-8.5 | r = 0.98 (scenario-invariant) |
| MaxEnt solver constraint check | r = 0.99998 |

## The math, in four movements

1. **Convex optimization** — MaxEnt ≡ Poisson point process, fit by elastic-net
   FISTA from scratch.
2. **Optimal transport** — entropic Sinkhorn displacement field + Coexistence
   Friction `F(x)=⟨T(x),∇H(x)⟩₊`.
3. **Spectral graph theory** — graph-Laplacian circuit current → conflict corridors.
4. **Algebraic topology** — cubical persistent homology of range fragmentation.
