# Literature Review — Modeling Human–Wildlife Interaction under Global Change

**Topic 25 (Pre-College Final Project):** *How can we model the ways that wildlife interact with humans and human-made communities?*
**Foundational reference:** Phillips, Anderson & Schapire (2006), *Maximum entropy modeling of species geographic distributions*, Ecological Modelling.

This review synthesizes the field across five threads: (1) the statistical foundations of species distribution models (SDMs); (2) the deep-learning revolution in SDMs; (3) sampling bias in presence-only data; (4) the mathematics of range dynamics, connectivity, and shape; and (5) human–wildlife conflict (HWC) modeling. Each thread ends with the **gap** our work exploits.

---

## Thread 1 — Statistical foundations of SDMs

MaxEnt (Phillips et al. 2006; Phillips & Dudík 2008) estimates a species' distribution as the maximum-entropy (Gibbs) distribution over a landscape subject to the constraint that feature expectations match empirical averages at presence sites. It is the single most-cited method in the field (>20k citations) and remains a workhorse for presence-only data.

The pivotal *mathematical* insight came later: **Renner & Warton (2013, Biometrics)** proved that **MaxEnt is exactly equivalent to an inhomogeneous Poisson point process (PPP) model**, differing only by a scale-dependent intercept. Warton & Shepherd (2010, *Annals of Applied Statistics*) framed presence-only data as a point process; Aarts et al. (2012) unified use-availability designs under the same umbrella; Renner et al. (2015, *MEE*) reviewed the point-process view. Fithian & Hastie (2013) showed MaxEnt is an infinitely-weighted logistic regression. **Consequence:** SDM is *convex optimization over an exponential family* — a Gibbs/log-linear model fit by (penalized) Poisson likelihood. This is the rigorous door we walk through: we can re-derive MaxEnt from first principles and fit it with elastic-net-penalized Poisson regression on a quadrature grid (Berman–Turner device).

Classic practical guidance: Elith et al. (2011) "statistical explanation of MaxEnt"; Merow et al. (2013) practical guide; Guisan & Thuiller (2005); Elith & Leathwick (2009, *Annual Review*). Feature classes, regularization (β multiplier), and clamping are the standard knobs.

**Gap:** The PPP/Gibbs view treats the landscape as a *bag of independent cells*. The **geometry** of the resulting probability surface — how its mass is arranged, connected, and how it *moves* under forcing — is discarded. No one has built the conflict/redistribution story *on top of* the transport and topology of the fitted intensity.

## Thread 2 — Deep learning SDMs

CNN-SDMs (Botella et al. 2018; Deneu et al. 2021, *PLOS Comp Biol*) exploit the spatial structure of environmental rasters and outperform classical SDMs when high-dimensional inputs (remote sensing) are available. A 2025 *PNAS* study reports CNNs outperforming other presence-only algorithms across birds, bats, reptiles and plants, especially for rare species with data augmentation. **DeepMaxent** (Zbinden et al. 2024, arXiv:2412.19217) folds the maximum-entropy principle into a multi-species neural network, inheriting MaxEnt's bias-correction while learning shared features. GeoLifeCLEF (Botella et al. 2023) is the benchmark driving this.

**Gap:** Deep SDMs improve *point predictions* of suitability but remain black boxes about *mechanism*. They do not yield an interpretable field of *where the range must go* or *why conflict emerges*. Our contribution is orthogonal and complementary: a mechanistic geometric layer that could sit on top of any suitability model, deep or classical.

## Thread 3 — Sampling bias in presence-only data

Presence-only records are haphazard: they oversample roads, cities, reserves. Phillips et al. (2009, *Ecological Applications*) introduced **target-group background (TGB)** — draw background from cells where *any* related species was recorded — to cancel shared observer bias. Fithian et al. (2015, *MEE*) pool survey + collection data across species to identify and remove bias. Warton et al. (2013), Barbet-Massin et al. (2012, pseudo-absence design), Merow et al. (2013), Kramer-Schadt et al. (2013) all stress that **background/bias choice matters as much as the model**. Spatial cross-validation (Roberts et al. 2017; Valavi et al. 2019 blockCV; Ploton et al. 2020) is now mandatory to avoid autocorrelation-inflated skill.

**Gap → we adopt best practice, not innovate here:** TGB backgrounds, spatial block CV, and a bias layer are used to make our suitability surfaces credible before the geometric analysis.

## Thread 4 — Range dynamics, connectivity, and shape (the math we deploy)

- **Optimal transport (OT).** Wasserstein distances quantify how much *mass must move* to turn one distribution into another — displacement, not just overlap. In ecology this is nascent: Ocean Mover's Distance (Sozou/… 2022, *Proc. R. Soc. A*) tracks biogeochemical province shifts; Gromov–Wasserstein compares ecological *networks* (Hung 2026, *MEE*; ICLR 2024). Entropic OT (Cuturi 2013, Sinkhorn) makes it computationally cheap and yields a smooth transport *plan*. **No one has used OT to build an interpretable displacement field of climate-forced range shift and couple it to human pressure.** Standard practice still uses centroid shifts or niche-overlap scalars (Schoener's D, Warren's I).
- **Circuit theory / spectral connectivity.** McRae et al. (2008, *Ecology*; Circuitscape) model gene/individual flow as electrical current on a resistance graph; effective resistance and current density identify corridors and pinch-points. Dickson et al. (2019) review its conservation uses. This is **spectral graph theory**: effective resistance = graph-Laplacian pseudoinverse; random-walk betweenness = commute times.
- **Topological data analysis (TDA).** Persistent homology summarizes the *shape* of data across scales: H0 = connected components (habitat patches), H1 = loops/holes (enclosed gaps). Applications to ecology are emerging (coral-reef zigzag persistence, Ulmer et al. 2019; spatial clustering). Habitat fragmentation is fundamentally a topological change, yet TDA is essentially unused for range fragmentation under climate change.

**Gap:** These three geometric tools have never been unified into a single, mechanistic account of how climate-forced redistribution creates conflict.

## Thread 5 — Human–wildlife conflict modeling

HWC prediction is dominated by black-box classifiers: random forests and 10-algorithm ensembles on human/climatic/landscape covariates (e.g., human–elephant conflict, Frontiers 2024; systematic reviews 2025), kernel-density hotspots, and MaxEnt on conflict-point occurrences. AI/early-warning systems (AAAI "Facilitating Human–Wildlife Cohabitation through Conflict Prediction") predict where/when interactions occur. Global human-pressure layers — Human Footprint (Venter et al. 2016, *Scientific Data*), Global Human Modification gHM (Kennedy et al. 2019, *Global Change Biology*; v3 2024) — quantify anthropogenic modification 0–1.

**Central weakness of the field:** conflict is modeled *correlatively and statically* — fit a classifier to past conflict points. There is **no forward-looking, mechanistic theory** that predicts *emergent* conflict from the physics of range redistribution: i.e., *conflict arises where climate forces a species to move into human-dominated space and cannot flow around it.*

---

## The gap we fill (one sentence)

> **The geometry of climate-forced species redistribution — the optimal-transport displacement field, its topological fragmentation, and its spectral connectivity through the human-pressure landscape — mechanistically predicts where human–wildlife conflict will emerge, and does so without ever training on conflict data.**

This is falsifiable, mathematically deep (convex optimization, entropic OT, spectral graph theory, persistent homology), and buildable from openly downloadable data (GBIF + WorldClim + gHM/Human Footprint).

---

## Key references (anchor set; ≥ the required threshold when combined with the manuscript bibliography)

1. Phillips, Anderson & Schapire (2006) *Ecol. Modelling* — MaxEnt. **[foundational]**
2. Phillips & Dudík (2008) *Ecography* — MaxEnt extensions/evaluation.
3. Elith et al. (2011) *Diversity & Distributions* — statistical explanation of MaxEnt.
4. Merow, Smith & Silander (2013) *Ecography* — practical guide to MaxEnt settings.
5. Renner & Warton (2013) *Biometrics* — MaxEnt ≡ Poisson point process. **[key math]**
6. Warton & Shepherd (2010) *Ann. Appl. Stat.* — point process for presence-only.
7. Renner et al. (2015) *Methods Ecol. Evol.* — point-process models review.
8. Fithian & Hastie (2013) *Ann. Appl. Stat.* — MaxEnt as weighted logistic regression.
9. Aarts, Fieberg & Matthiopoulos (2012) *MEE* — use-availability unification.
10. Phillips et al. (2009) *Ecol. Applications* — target-group background / sample bias.
11. Fithian et al. (2015) *MEE* — bias correction by pooling multi-species.
12. Barbet-Massin et al. (2012) *MEE* — pseudo-absence selection.
13. Elith & Leathwick (2009) *Annu. Rev. Ecol. Evol. Syst.* — SDM review.
14. Guisan & Thuiller (2005) *Ecology Letters* — predicting distributions.
15. Roberts et al. (2017) *Ecography* — cross-validation with spatial dependence.
16. Valavi et al. (2019) *MEE* — blockCV.
17. Ploton et al. (2020) *Nature Communications* — spatial autocorrelation inflates skill.
18. Hijmans et al. (2005) *Int. J. Climatology* — WorldClim v1.
19. Fick & Hijmans (2017) *Int. J. Climatology* — WorldClim 2.
20. Booth et al. (2014) — BIOCLIM history / bioclimatic variables.
21. Deneu et al. (2021) *PLOS Comp. Biol.* — CNN-SDM captures spatial structure.
22. Botella et al. (2018) — CNN species distribution.
23. (2025) *PNAS* — CNNs outperform presence-only SDM algorithms.
24. Zbinden et al. (2024) arXiv:2412.19217 — DeepMaxent.
25. Botella et al. (2023) *GeoLifeCLEF*.
26. Cuturi (2013) *NeurIPS* — Sinkhorn distances / entropic OT.
27. Peyré & Cuturi (2019) — Computational Optimal Transport (monograph).
28. Villani (2009) — Optimal Transport, Old and New.
29. Ocean Mover's Distance (2022) *Proc. R. Soc. A* — OT for ocean province shifts.
30. Hung et al. (2026) *MEE* — Gromov–Wasserstein for ecological networks.
31. McRae et al. (2008) *Ecology* — Circuitscape / circuit theory connectivity.
32. Dickson et al. (2019) *Conservation Biology* — circuit-theory review.
33. McRae & Beier (2007) *PNAS* — circuit theory in ecology/evolution.
34. Edelsbrunner & Harer (2010) — Computational Topology / persistent homology.
35. Carlsson (2009) *Bull. AMS* — Topology and data.
36. Ghrist (2008) *Bull. AMS* — Barcodes: persistent topology.
37. Bauer (2021) *J. Appl. Comput. Topol.* — Ripser.
38. Ulmer, Ziegelmeier & Topaz (2019) *PLoS ONE* — TDA of biological aggregation / reef.
39. Venter et al. (2016) *Scientific Data* — global Human Footprint.
40. Kennedy et al. (2019) *Global Change Biology* — Global Human Modification (gHM).
41. Tucker et al. (2018) *Science* — human footprint reduces mammal movement.
42. Di Minin et al. (2021) — global HWC review.
43. Nyhus (2016) *Annu. Rev. Environ. Resour.* — human–wildlife conflict.
44. Chapron et al. (2014) *Science* — large carnivore recovery in human-dominated Europe.
45. AAAI (2021) — Facilitating human–wildlife cohabitation through conflict prediction.
46. Frontiers Ecol. Evol. (2024) — HWC hotspot prediction, Daba Mts.
47. Systematic review (2025) *Discover Environment* — HWC modelling approaches.
48. Pateiro-López & Rodríguez-Casal — alpha shapes / range estimation.
49. Broennimann et al. (2012) *GEB* — niche overlap in environmental space (Schoener's D).
50. Warren et al. (2008) *Evolution* — niche identity / overlap statistics (I, D).
51. Thuiller et al. (2005) *Global Change Biology* — climate change range projections.
52. IPCC AR6 / CMIP6 SSP scenarios — future climate forcing.
53. Cobos et al. (2019) *kuenm* / ENMeval (Muscarella et al. 2014) — model selection for MaxEnt.
54. Anderson & Raza (2010) — extent choice effects on SDM.

(The manuscript's reference list expands these with method-specific citations for Sinkhorn stability, spectral graph theory, and persistence stability theorems.)
