# Research Plan — *The Geometry of Coexistence*

**Full title (working):** *The Geometry of Coexistence: optimal transport, spectral connectivity, and persistent homology of climate-forced species redistribution predict emergent human–wildlife conflict*

**Target venue framing:** methods-forward computational ecology with a mechanistic, mathematically novel core (Nature / Nature Communications / PNAS / NeurIPS Climate track aspirational; realistically a strong *Methods in Ecology & Evolution* / *Ecography* paper).

---

## 1. Thesis

Human–wildlife conflict is currently modeled *correlatively and retrospectively*. We propose a *mechanistic, prospective* theory: **conflict emerges where climate change forces a species' suitable habitat to move into human-dominated space and the landscape's connectivity cannot route the animals around that pressure.** We formalize "forced to move" with **entropic optimal transport**, "cannot route around" with **spectral graph connectivity (circuit theory)**, and "fragmentation exposure" with **persistent homology** — all built on a from-scratch **maximum-entropy / Poisson-point-process** suitability model. Crucially, the conflict prediction *never trains on conflict data*, so validating it against independent conflict records is a genuine out-of-sample test of the mechanism.

## 2. Novel contributions (what is actually new)

1. **Entropic Displacement Field (EDF).** Treat present and future suitability surfaces as probability measures; solve the Sinkhorn optimal-transport problem between them to obtain (a) a scalar **Wasserstein range-shift distance** and (b) a **vector displacement field** `T(x)` giving where each unit of habitat mass must migrate. New to terrestrial SDM.
2. **Coexistence Friction functional.** Define `F(x) = ⟨ T(x), ∇H(x) ⟩₊` — the positive part of the inner product between the displacement field and the gradient of human modification `H`. High `F` = species forced *up the human-pressure gradient* = mechanistic conflict hotspot. A single, interpretable, differentiable scalar field.
3. **Spectral corridor bottlenecks.** Build a resistance surface `R = f(1−suitability, H)`; compute effective resistance and random-walk current (graph-Laplacian pseudoinverse) to find pinch-points where displacement must funnel through human landscape. Implemented from scratch (spectral graph theory), not Circuitscape.
4. **Topological fragmentation dynamics.** Sublevel-set persistent homology (H0/H1) of the suitability surface, present vs future; a **persistence-based fragmentation index** and its change quantify emergent edge exposure. Bottleneck/Wasserstein distance between persistence diagrams measures structural range change.
5. **Unified Coexistence Risk Index (CRI)** combining EDF friction, spectral bottleneck current, and topological edge exposure — and **validated against independent human–wildlife conflict / occurrence-in-human-areas signals** the model never saw.

## 3. Mathematical core (the "wizardry")

- **SDM as convex optimization.** Re-derive MaxEnt as the Gibbs distribution maximizing entropy s.t. feature-expectation constraints; show its Lagrangian dual is elastic-net-penalized Poisson likelihood (Berman–Turner quadrature; Renner & Warton 2013). Implement an **elastic-net Poisson IRLS / coordinate-descent solver from scratch**; verify KKT/feature-matching conditions numerically.
- **Entropic OT.** Solve `min_P ⟨P,C⟩ − ε H(P)` s.t. marginals, via **Sinkhorn iterations** (log-domain, stabilized). Recover barycentric displacement map. Report Sinkhorn divergence (debiased).
- **Spectral graph theory.** Grid → weighted graph; combinatorial Laplacian `L`; effective resistance `r(i,j)=(e_i−e_j)ᵀ L⁺ (e_i−e_j)`; random-walk / current-flow betweenness for corridor current.
- **Persistent homology.** Cubical/Vietoris–Rips filtration on the suitability field via `ripser`; persistence landscapes; bottleneck distance; stability theorem guarantees robustness to noise.
- **Uncertainty & inference.** Spatial block bootstrap for CRI CIs; permutation null for the friction–conflict association; spatial-block cross-validation for the SDM.

## 4. Study system & data (all openly downloadable, no institutional login)

- **Occurrences — GBIF REST API** (no auth for `/occurrence/search`; paginated). Charismatic, conflict-prone European large mammals with dense records and active range dynamics:
  - Brown bear *Ursus arctos*, Grey wolf *Canis lupus*, Eurasian lynx *Lynx lynx*, Golden jackal *Canis aureus* (rapidly expanding — strong shift signal), Wild boar *Sus scrofa*, Red fox *Vulpes vulpes* (urban interface), Roe deer *Capreolus capreolus* (prey/vehicle-collision interface). Target ~5–8 species.
  - Spatial-thin to ~1 record / grid cell; **target-group background** from the pooled multi-species record set to cancel observer bias.
- **Climate — WorldClim 2.1** bioclimatic variables bio1–bio19, present (1970–2000) and a **future scenario** (SSP2-4.5 or SSP5-8.5, 2081–2100). Direct GeoTIFF download from `geodata.ucdavis.edu` / worldclim.org mirrors. 10 arc-min (≈18 km) baseline; 5 arc-min if bandwidth allows.
- **Human pressure — Global Human Modification (gHM)** or **Human Footprint (Venter et al. 2016)**, whichever downloads cleanly (Figshare/Zenodo/SEDAC GeoTIFF). Provides `H(x) ∈ [0,1]`.
- **Domain:** Europe (well-sampled; documented carnivore recovery, Chapron et al. 2014). Bounding box ≈ lon [-12, 40], lat [35, 72].

## 5. Pipeline (implementation order)

0. **Config & IO** (`00_config.py`, `io_utils.py`): domain grid, CRS, raster read/resample to common grid.
1. **Data acquisition** (`10_download_*.py`): GBIF occurrences, WorldClim present+future, human modification. Cache to `data/raw`.
2. **Preprocess** (`20_build_covariates.py`): stack bioclim to common grid; spatial thinning; TGB background; feature engineering (linear/quadratic/product/hinge features à la MaxEnt).
3. **SDM core** (`30_maxent_ppm.py`): from-scratch elastic-net Poisson-PPM MaxEnt; spatial block CV (AUC, TSS, Boyce index, deviance); predict present & future suitability per species; bias layer.
4. **Optimal transport** (`40_transport.py`): Sinkhorn EDF, Wasserstein shift, displacement field, Coexistence Friction `F`.
5. **Connectivity** (`50_connectivity.py`): resistance surface, Laplacian, effective resistance, current-flow corridors & bottlenecks.
6. **Topology** (`60_topology.py`): sublevel-set persistent homology; fragmentation index; present→future persistence-diagram distances.
7. **Risk synthesis + validation** (`70_risk.py`): Coexistence Risk Index; validate against held-out occurrences in high-`H` cells and (if obtainable) conflict signals; permutation nulls; bootstrap CIs.
8. **Figures** (`80_figures/`): four flagship multi-panel figures, each 4 sub-panels of dense, niche visualizations.
9. **Manuscript + 1-pager + website**.

## 6. The four flagship figures (each = 4 sub-panels, publication-grade)

- **Figure 1 — The Framework & Data.** (a) map of multi-species occurrence density with TGB background; (b) environmental space (PCA of bioclim) with species niches as density contours; (c) schematic of the Gibbs→PPP→OT→topology pipeline; (d) SDM performance (spatial-CV AUC/Boyce) ridgeline across species.
- **Figure 2 — Entropic Displacement.** (a) present vs future suitability (bivariate map); (b) the OT displacement field as streamlines/quiver over Europe; (c) Wasserstein shift distance vs latitude/elevation; (d) Coexistence Friction hotspot map with human-modification contours.
- **Figure 3 — Connectivity & Topology.** (a) resistance surface + current-flow corridors; (b) effective-resistance bottleneck ("pinch-point") map; (c) persistence barcodes/diagram present vs future; (d) persistence landscape + fragmentation-index change.
- **Figure 4 — Coexistence Risk & Validation.** (a) unified CRI map (hexbin/relief); (b) CRI vs independent conflict/human-interface validation (ROC + calibration); (c) permutation null vs observed friction–conflict association; (d) species-resolved risk decomposition (small-multiples radar / bump chart).

Aesthetic standard: perceptually-uniform colormaps, minimal chartjunk, consistent typography, bespoke bivariate/topological encodings, dark-and-light-safe. "Brain-melting" density with clarity.

## 7. Validation & honesty guardrails

- Report spatial-CV metrics, not naive resubstitution.
- Permutation and spatial-block-bootstrap nulls for every headline association.
- Sensitivity to: OT entropy `ε`, grid resolution, feature classes, climate scenario, human-pressure layer choice.
- Explicit limitations: correlative niche assumption, occurrence bias residuals, coarse resolution, equilibrium assumption, no dispersal dynamics (we quantify *demand* for movement, not realized movement).

## 8. Risk register / pivots

- **gHM download blocked →** fall back to Human Footprint (Venter 2016) or GHS population/built-up proxies.
- **WorldClim future blocked →** derive plausible warming perturbation (uniform + lapse-rate) as scenario, clearly labeled; or use CHELSA mirror.
- **GBIF rate limits →** cap per-species records, thin, cache aggressively.
- **rasterio/gdal issues →** already resolved (rasterio 1.5 installed).
- **Persistent homology too slow on full grid →** downsample field / use cubical complex on coarsened raster.

## 9. Deliverables

1. Reproducible codebase (`project/src`).
2. Four flagship figures (`project/figures`).
3. Full manuscript (`project/manuscript`), Nature-style.
4. Plain-language 1-pager for non-technical teammates.
5. Interactive website (Artifact) summarizing the story.
