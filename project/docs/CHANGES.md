# CHANGES — website overhaul & figure revisions

This document records every change made during the interactive-website overhaul,
in the interest of full transparency. **No numerical result changed.** Every
figure and interactive element is regenerated from the same committed pipeline
outputs (`results/sdm.npz`, `results/analysis.npz`, `results/summary.json`,
`results/robustness.json`). Nothing was invented, inflated, or cherry-picked.

## Figures

1. **Colourblind-safe palette.** The 7-species categorical palette was switched to
   the **Okabe–Ito** palette (validated distinguishable under deuteranopia,
   protanopia, and tritanopia). Every figure that distinguishes species by colour
   now also uses a **redundant marker shape** (circle/square/triangle/diamond/…),
   so colour is never the only channel. *Cosmetic only — no data changed.*
   - Sequential maps already used perceptually-uniform, red-green-safe colormaps
     (navy→teal→gold for suitability; dark→ember→gold for risk/friction;
     dark→blue→cyan for current). The gain/loss bivariate map uses blue↔red, which
     is colourblind-safe. These were verified and kept.

2. **TSS removed from Figure 1d and from the website skill chart.** Rationale
   (methodological, not cosmetic): the True Skill Statistic requires a hard
   probability threshold and genuine absence data, neither of which fits
   presence-only occurrence records. We report **AUC** and the **presence-only
   Boyce index** instead — the standard, defensible choice.
   - **The TSS values were NOT deleted from the data.** They remain in
     `results/sdm_metrics.json`; they are simply no longer displayed. This is a
     reporting choice with a stated justification, not selective hiding of a weak
     number (the low TSS values are themselves interpretable — they reflect
     hard-to-threshold generalist species).

3. **New figure — `figureSDM_present_future`.** A present-vs-2090 species-distribution
   panel (one map per species: filled present suitability, dashed 2090 core-range
   boundary, mean-displacement arrow). Built entirely from existing `present__*`
   and `future__*` suitability grids in `sdm.npz`. **New visualization, no new data.**

## Display transform (labelled, science unchanged)

- The SDM maps (static figure + interactive viewer) apply a **per-species contrast
  stretch** for display: suitability is divided by the species' 98th-percentile
  value so the habitat is visible (cloglog suitability is concentrated at low
  values). This is a *display normalization only*, is clearly labelled "relative
  suitability", and the future epoch is scaled by the **same factor** so the
  present→2090 change stays comparable. It does not alter any computed result.

## Website (new)

- The site was rebuilt from a single inline HTML file into a **clean multi-file
  static app** (HTML + CSS + JS modules + JSON data + image assets), hosted on
  Vercel. This enables interactivity that GitHub Pages / inline artifacts could not.
- **Interactive figures**: hoverable climatic-niche chart, hoverable skill dot-plot,
  and a present↔2090 suitability **wipe-and-hover map viewer** — all driven by real
  data exported from the pipeline via `src/export_web.py` (`meta.json`, `skill.json`,
  `niche.json`, `sdm_grids.json`, `risk_grid.json`).
- **Expanded Results, Significance, and Future-Research sections** — all numbers
  match the manuscript/`summary.json`; no new scientific claims were introduced.
- **Escape-room game** (`assets/js/game.js`): a four-station educational game whose
  every fact mirrors content already on the site (habitat models use climate data;
  warming pushes species ~484 km north; conflict occurs in farmland/cities; the risk
  map predicts hotspots without historical conflict data). **No new information.**

## Reproducibility

- `src/export_web.py` regenerates all website data/images from committed results.
- `run_pipeline.sh` now regenerates the new figure and web assets.
- The legacy single-file `build_site.py` is retained for reference but is no longer
  the site source of truth.
