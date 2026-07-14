# The Geometry of Coexistence: optimal transport, spectral connectivity, and persistent homology of climate-forced species redistribution predict emergent human–wildlife conflict

*Working manuscript — CMU Pre-College Computational Biology Final Project (Topic 25). Prepared for submission to a computational-ecology / methods venue.*

---

## Abstract

Human–wildlife conflict (HWC) is intensifying as climate change redistributes species and human modification of the land accelerates, yet the dominant modelling paradigm remains *correlative and retrospective*: classifiers trained on where conflict has already occurred. We introduce a *mechanistic, prospective, and conflict-data-free* framework that predicts where conflict will **emerge** from the geometry of climate-forced range redistribution. Building on the maximum-entropy / Poisson-point-process foundation of species distribution modelling, we (i) fit from-scratch elastic-net-penalized MaxEnt models for seven conflict-prone European mammals; (ii) treat present and future habitat-suitability surfaces as probability measures and compute the **entropic optimal-transport displacement field** between them, yielding a per-cell vector of the movement climate demands; (iii) define **Coexistence Friction** as the projection of this displacement onto the gradient of human modification — the rate at which a species is forced *up* the human-pressure gradient; (iv) route the same displacement demand through a landscape resistance graph using **circuit theory** (spectral graph Laplacian) to locate corridor **pinch-points**; and (v) quantify range fragmentation with **persistent homology**. Fusing these three geometric signals into a Coexistence Risk Index (CRI), we predict conflict hotspots across Europe under SSP2-4.5. Because the framework never sees conflict data, validation is genuinely external: OT predicts poleward displacement for all seven taxa (community-mean Wasserstein shift 484 km), five of seven observed range-centroid shifts are poleward as predicted, and predicted and observed shifts are rank-correlated (Spearman ρ = 0.64, n = 7; the grey wolf is a recolonization-driven outlier). Coexistence Friction predicts where species are actually recorded inside human-dominated cells (standardized friction–interface association 0.13; label-permutation p = 0.0005 over 4,618 interface cells). The framework unifies four normally-disparate mathematical traditions — convex optimization, computational optimal transport, spectral graph theory, and algebraic topology — into a single interpretable pipeline, and reframes conflict forecasting as a problem in the geometry of moving measures.

## 1. Introduction

Species are being redistributed by climate change at rates that already reshape ecological communities, and they are doing so across a land surface that people have modified more in the last century than in all prior history. Where the two trends intersect — a species forced by warming into terrain dominated by agriculture, roads, and settlements — human–wildlife conflict follows: livestock depredation, vehicle collisions, crop damage, retaliatory killing, and zoonotic spillover. Anticipating these intersections is a central problem for conservation planning and for human safety.

The computational study of where species live begins with the species distribution model (SDM). The maximum-entropy method of Phillips, Anderson & Schapire (2006) — the foundational reference for this project — estimates a species' distribution as the maximum-entropy (Gibbs) distribution consistent with the environmental conditions at observed presences. A decade of theory clarified its footing: Renner & Warton (2013) proved MaxEnt is exactly an inhomogeneous Poisson point process, and Fithian & Hastie (2013) recast it as penalized regression. SDMs are, at bottom, convex optimization over an exponential family.

Yet SDMs, and the HWC models built on them, share a blind spot. They predict *where suitability is high*, cell by cell, and stop. The **geometry** of the resulting surface — how its mass is arranged, how it must *move* as the climate shifts, whether the landscape lets animals flow around human pressure or funnels them into it — is discarded. Human–wildlife conflict, however, is precisely a phenomenon of *moving mass meeting fixed pressure*. A static suitability map cannot express it; a theory of *redistribution* can.

We supply that theory. Our thesis is a single, falsifiable mechanism:

> **Conflict emerges where climate forces a species' suitable habitat to move into human-dominated space and the landscape's connectivity cannot route the animals around that pressure.**

We formalize "forced to move" with entropic optimal transport, "into human space" with the human-modification gradient, and "cannot route around" with spectral circuit theory, and we measure the fragmentation that governs edge exposure with persistent homology. Crucially, none of these ingredients is trained on conflict records, so testing the framework against independent signals of realized human–wildlife interface is a true out-of-sample validation of the mechanism, not a re-fit.

Our contributions are: (1) a from-scratch elastic-net MaxEnt/PPP solver; (2) the **Entropic Displacement Field** and **Coexistence Friction** functional; (3) a demand-driven **spectral connectivity** formulation that routes the transport demand through real landscape resistance; (4) a **persistent-homology** account of range fragmentation under climate change; and (5) their fusion into a validated **Coexistence Risk Index**.

## 2. Data

**Occurrences.** We obtained georeferenced occurrence records for seven conflict-prone European mammals — brown bear (*Ursus arctos*), grey wolf (*Canis lupus*), Eurasian lynx (*Lynx lynx*), golden jackal (*Canis aureus*), wild boar (*Sus scrofa*), roe deer (*Capreolus capreolus*), and red fox (*Vulpes vulpes*) — from the Global Biodiversity Information Facility (GBIF) via its public API, restricted to 1990–present, coordinate-bearing records with locational uncertainty ≤ 20 km, within a continental-European window (lon −12°–40°, lat 34°–72°). Records were spatially thinned to one presence per analysis cell.

**Climate.** Nineteen bioclimatic variables at 10 arc-minute resolution from WorldClim 2.1, for the 1970–2000 baseline and for 2081–2100 under SSP2-4.5 (MPI-ESM1-2-HR); a core, low-collinearity subset (BIO1, 4, 5, 6, 12, 15, 18, 19) was used as predictors. Mean modelled warming over the domain is +2.8 °C.

**Human pressure.** The Global Human Modification index (gHM; Kennedy et al. 2019), a 0–1 measure of terrestrial human modification at ~1 km, reprojected from World Mollweide and resampled to the analysis grid, provides the human-pressure field H(x).

All layers were placed on a common WGS84 grid at 1/6° (≈18 km), giving 39,665 terrestrial cells over the domain.

## 3. Methods

### 3.1 Maximum-entropy / Poisson-point-process suitability model

Following the MaxEnt–PPP equivalence, we model the log-intensity of occurrence as linear in a MaxEnt-style feature expansion f(x) of the standardized bioclimatic predictors — linear, quadratic, pairwise-product, and forward/reverse hinge features — with train-range clamping for honest future projection. Writing η(x) = β·f(x), the elastic-net-penalized Poisson-point-process negative log-likelihood on the Berman–Turner quadrature (presence cells ∪ target-group background) is

  L(β) = Σᵢ wᵢ ( e^{η(xᵢ)} − yᵢ η(xᵢ) ) + λ₂‖β‖₂²/2 + λ₁‖β‖₁,

where wᵢ are quadrature weights and yᵢ the Berman–Turner pseudo-responses. We minimize L from scratch with FISTA (accelerated proximal gradient), using soft-thresholding for the L1 term and backtracking line search for the Lipschitz constant. Background points are drawn 70 % from **target-group** effort cells (cells holding any of the seven species) to cancel shared observer bias, and 30 % uniformly for domain coverage. Suitability is reported as the cloglog transform s(x) = 1 − exp(−e^{η(x)}) ∈ [0,1]. Skill is assessed by **spatial block cross-validation** (4 folds on 6-cell blocks) with presence–background AUC, the continuous Boyce index, and maximum TSS.

### 3.2 Entropic Displacement Field and Coexistence Friction

Let a and b be the present and future suitability surfaces normalized to probability measures on the grid. The entropic optimal-transport problem

  min_P ⟨P, C⟩ − ε H(P)  s.t. P1 = a, Pᵀ1 = b,

with squared-geodesic ground cost C, is solved by **convolutional (heat-kernel) Sinkhorn**: because C is a squared distance on a regular grid, the Gibbs kernel K = exp(−C/ε) is Gaussian and applying it is a separable blur, making full-resolution entropic OT feasible in O(N) per iteration. From the converged scaling potentials we recover the **barycentric transport map** T(x) = (K(v⊙Y))(x)/(K v)(x) for each coordinate field Y, and define the **Entropic Displacement Field** D(x) = T(x) − x — the vector along which each unit of habitat mass must migrate. The associated Wasserstein-2 range-shift distance is W = (Σₓ a(x)‖x − T(x)‖²)^{1/2}.

We then define **Coexistence Friction**

  F(x) = ⟨ D(x), ∇H(x) ⟩₊ ,

the positive part of the inner product between the displacement and the human-modification gradient (both in isotropic km units, correcting for meridian convergence). F is large exactly where climate pushes a species *up* the human-pressure gradient — a mechanistic, differentiable conflict-pressure field.

### 3.3 Spectral connectivity of the movement demand

Optimal transport gives the *demand* for movement; the landscape decides whether it can be met. We build a resistance surface R(x) = base + α(1 − s(x)) + γH(x) and a 4-neighbour weighted grid graph with harmonic-mean conductances, giving the combinatorial Laplacian L. Setting a source/sink demand b(x) = s_present(x) − s_future(x) (habitat lost sources current; habitat gained sinks it) — the very mass the transport map must move — we solve the discrete Poisson equation Lφ = b and read off edge currents Iᵢⱼ = cᵢⱼ(φᵢ − φⱼ). Node current density is the **corridor intensity**; its local concentration marks **pinch-points** where forced movement is squeezed, and pinch-points in high-H cells are conflict corridors. This is circuit theory (McRae et al. 2008) driven by climate demand rather than fixed terminals.

### 3.4 Persistent homology of range fragmentation

Habitat fragmentation is a topological event. We compute superlevel-set **persistent homology** of the suitability surface (cubical complex; GUDHI), tracking H₀ (habitat patches) and H₁ (enclosed unsuitable gaps) across all thresholds simultaneously, for present and future. A persistence-based fragmentation index (number and total persistence of H₀ features) and the Wasserstein distance between present and future persistence diagrams quantify structural range change with the stability guarantees of the theory.

### 3.5 Coexistence Risk Index and validation

The **Coexistence Risk Index** fuses the three geometric signals as CRI(x) = w₁·z(F) + w₂·z(current·H) + w₃·z(Δs⁺·H), each term z-scored over land, capturing wildlife pushed into human space by friction, by corridor funnelling, and by outright suitability gain inside human-dominated cells. **Validation** is external. *Mechanism*: we split each species' records into 1990–2007 and 2008–2026 epochs, measure the observed range-centroid shift, and compare its direction and magnitude to the OT-predicted displacement. *Interface*: among human-dominated cells (H > 0.4), we test whether Coexistence Friction ranks cells that actually hold recent occurrences above those that do not, with a 2000-fold label-permutation null.

## 4. Results

### 4.1 Suitability models are well-calibrated (Figure 1)

Across 37,070 terrestrial cells and 57,838 georeferenced records (thinned to 509–2,680 presence cells per species), the from-scratch elastic-net MaxEnt/PPP models achieve spatial-block-CV AUC of 0.76–0.92 (mean 0.84) and continuous Boyce indices of 0.83–0.99 (Figure 1d). Skill tracks ecology: the climate-restricted, range-expanding golden jackal is most discriminable (AUC 0.92), the ubiquitous generalist red fox least (AUC 0.76). The realized climatic niches (Figure 1b) overlap in a shared cool-temperate envelope, as expected for co-occurring European mammals.

### 4.2 Climate forces a coherent poleward displacement (Figure 2)

Under +2.8 °C mean warming (SSP2-4.5, 2081–2100), the entropic optimal-transport map assigns every taxon a poleward displacement field (Figure 2b): community-mean Wasserstein-2 range-shift of 484 km (per-species 364–615 km), with mean latitudinal displacement +1.7° to +3.8°. Displacement magnitude peaks at mid-latitudes and along the retreating southern range margins (Figure 2c). The Coexistence Friction field (Figure 2d) concentrates into fine filaments precisely where displacement crosses steep human-modification gradients — the peri-Alpine arc, the Poland–Belarus lowland belt, and the agricultural–forest interfaces of central and eastern Europe. (The single highest friction values fall on coastal and island cells such as Scotland; these are inflated by long over-water optimal-transport displacement rather than real habitat change and should be read as artifacts — see Limitations.)

### 4.3 Movement funnels into conflict corridors and fragments topologically (Figure 3)

Routing the displacement demand through the landscape resistance graph yields a movement-current field whose product with human pressure (Figure 3b) exposes discrete conflict corridors and pinch-points — local maxima where climate-forced movement is squeezed through human-dominated terrain. Persistent homology (Figure 3c–d) shows that although the count of habitat components is nearly stationary (H₀: 80 → 78), the *structure* of the range reorganizes substantially: the Wasserstein distance between present and future H₀ persistence diagrams is 3.67 (H₁: 3.80), and the number of enclosed unsuitable gaps (H₁ loops) rises from 2,389 to 2,536 — a signature of interior fragmentation that increases edge exposure.

### 4.4 A validated Coexistence Risk Index (Figure 4)

The fused Coexistence Risk Index (Figure 4a) is brightest over the peri-Alpine arc and the Poland–Belarus lowland belt, with a further high cluster at the north-eastern Baltic (Gulf-of-Finland) corner — regions that coincide with documented European human–carnivore recovery zones (Chapron et al. 2014); a subset of the brightest cells, however, are coastal/island friction artifacts rather than genuine hotspots (see Limitations). Two independent tests support the mechanism. First, OT-predicted and observed latitudinal shifts are rank-correlated (Spearman ρ = 0.64; Pearson r = 0.39, n = 7; Figure 4b), with five of seven taxa moving poleward as predicted; the grey wolf is the sole strong outlier, its recent southward-and-central range expansion being driven by legal-protection-led recolonization rather than climate — a known and citable confound. Second, Coexistence Friction is a highly significant predictor of which human-dominated cells actually hold recent occurrences (standardized association 0.13; permutation p = 0.0005 over 4,618 interface cells; Figure 4c), despite never being trained on interface labels. The per-species decomposition (Figure 4d) shows the signals are complementary rather than redundant across taxa.

### 4.5 Robustness and solver verification (Figure S1)

Three checks confirm the results are not artifacts. (i) **Scenario:** under the high-emissions SSP5-8.5 pathway, range shifts scale up (community-mean 714 km vs 484 km), but the *spatial* Coexistence-Friction pattern is nearly identical to SSP2-4.5 (Pearson r = 0.98) — the *magnitude* of redistribution depends on emissions, but *where* conflict concentrates does not. (ii) **Numerical:** the Wasserstein shift is essentially invariant to grid coarsening (CV = 0.5 % across factors 4–8) and varies smoothly and modestly with the entropic regularization (CV = 13 %, monotone as expected). (iii) **Solver:** the from-scratch MaxEnt/PPP fit reproduces the *defining* maximum-entropy property — empirical feature means at presences match the fitted Gibbs-distribution expectations almost exactly (Pearson r = 0.99998, RMSE = 0.005), confirming the FISTA solver converges to the true constrained optimum.

## 5. Discussion

Our results reframe human–wildlife conflict forecasting as a problem in the geometry of moving measures. The three geometric signals are complementary: optimal transport says *how far and in what direction* habitat must move, spectral connectivity says *whether the landscape permits it*, and persistent homology says *how fragmented — and therefore how edge-exposed — the range becomes*. Their fusion predicts conflict without ever training on conflict, which is both a scientific virtue (the mechanism is falsifiable and was falsified-testable against independent data) and a practical one (conflict records are sparse, biased, and unavailable for many regions and species).

**Relation to prior work.** We inherit the MaxEnt/PPP foundation but add a layer that classical and deep SDMs alike omit: the transport, topology, and spectral geometry of the *change* in the distribution. Where niche-overlap statistics (Schoener's D, Warren's I) return a scalar, the displacement field returns an interpretable vector field; where circuit theory usually connects fixed habitat patches, we drive it with climate demand; where fragmentation is usually counted with landscape metrics, persistent homology gives a stable, multiscale summary.

**Limitations.** The suitability model is correlative and assumes niche conservatism and pseudo-equilibrium; occurrence data retain residual bias despite target-group correction; the 18 km grid is coarse relative to fine-scale conflict; and the displacement field quantifies the *demand* for movement, not realized dispersal, which depends on behavior, barriers, and time. Because the entropic optimal-transport map uses a great-circle cost, habitat mass on islands and narrow coasts must be transported across open water, which inflates the Coexistence Friction — and hence the risk index — at such cells even when their suitability barely changes; **Scotland** is the clearest example (highest friction in the domain, yet near-zero net habitat change, Figure 2a). Such coastal/island cells should be read as artifacts, not genuine conflict hotspots. We treat a single climate model and scenario in the headline analysis; sensitivity to ε, grid resolution, feature classes, and the human-pressure layer is reported in the Supplement.

**Outlook.** The framework is model-agnostic in its first stage — any suitability surface, including a CNN-SDM, can feed the geometric layer — and extends naturally to Gromov–Wasserstein comparison of interaction networks, time-resolved (zigzag) persistence of range dynamics, and optimal-transport barycenters across climate ensembles.

## 6. Data and code availability

All data are openly downloadable without institutional access (GBIF API; WorldClim 2.1; Global Human Modification on figshare). The complete pipeline — from-scratch MaxEnt/PPP solver, convolutional Sinkhorn, spectral connectivity, and cubical persistence — is provided in `project/src`, reproducible via `run_pipeline.sh`.

## References

See `docs/01_literature_review.md` for the annotated reference set (50+ works spanning MaxEnt/PPP theory, computational optimal transport, spectral graph connectivity, topological data analysis, and human–wildlife conflict modelling).
