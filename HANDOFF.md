# PROJECT HANDOFF — *The Geometry of Coexistence*

> **Read this first.** This document is a complete, self-contained brief for an AI (or
> human) picking up this project cold, with no access to prior chat history. After
> reading it you should be able to run the pipeline, regenerate every figure, edit the
> website and game, and deploy — with full context on *why* each decision was made.
> **Keep this document updated after any future change** (there is a maintenance
> checklist at the bottom).

Last updated: 2026-07-14. Repo: `https://github.com/oreopengguin/cmu-wildlife-conflict`
Live site: `https://cmu-wildlife-conflict.vercel.app/`
This file **is committed to the repo** (at the repo root), so it travels with a fresh clone.
It was validated by a from-scratch simulated handoff (fresh AI context, no chat history) that
ran the verifications in §2/§5/§7 successfully.

---

## −1. 60-SECOND QUICK START (run this first)

```bash
cd /Users/zacharyzhang/cmu-final-project
bash verify.sh          # executable health check: env, data, site, git hygiene, reproducibility
```
If it prints **"Environment is healthy"** (35/35), you can edit/regenerate/deploy with
confidence. If any line shows ✗, read it and the matching section below. `verify.sh` is the
fastest way to know the project is in a workable state without reading everything.

**The three commands you'll use most:**
```bash
# 1. run a pipeline script / regenerate a figure (ALWAYS from src, with the venv):
cd project/src && ../.venv/bin/python figSDM.py
# 2. refresh website data+images after any science/figure change:
cd project/src && ../.venv/bin/python export_web.py
# 3. commit + deploy (NO co-author trailer; Vercel auto-redeploys):
cd /Users/zacharyzhang/cmu-final-project && export PATH="/opt/homebrew/bin:$PATH" GH_CONFIG_DIR=~/.ghconfig
git add -A && git commit -m "..." && git push origin main
```

## 0. TL;DR

This is a CMU Pre-College Computational Biology **final project** (Topic 25: *"How can we
model the ways wildlife interact with humans and human-made communities?"*, foundational
reference = MaxEnt / Phillips, Anderson & Schapire 2006). The owner wanted a maximally
ambitious, *Nature/NeurIPS-aspirational* deliverable.

**The science, in one sentence:** *You can forecast where human–wildlife conflict will
emerge in Europe purely from the geometry of how climate forces species' habitat to move —
without ever training on conflict data.*

**Deliverables that exist and are done:**
- A reproducible Python pipeline (from-scratch MaxEnt, optimal transport, spectral
  connectivity, persistent homology, risk synthesis, robustness).
- 6 publication-grade figures (4 main + 1 supplementary + 1 SDM present/2090).
- A full Nature-style manuscript (`project/manuscript/manuscript.md`).
- An **interactive website** (multi-file static app on Vercel) with interactive charts, a
  present↔2090 map viewer, a large results section, future-research ideas, and a
  **four-room educational escape-room game**.
- Two plain-language one-pagers + a literature review + a research plan + a CHANGES log.

**Absolute constraint — HONESTY:** Every number, figure, and interactive element must come
from the real committed pipeline output. Never invent, inflate, or cherry-pick. Any change
to how results are presented must be documented in `project/docs/CHANGES.md`.

---

## 1. Working directory & repo layout

- **Working dir / git repo root:** `/Users/zacharyzhang/cmu-final-project/`
- The actual project lives in the `project/` subfolder.
- The course assignment PDF at the repo root is **gitignored** (third-party material).
- `data/` (2.6 GB) and `.venv/` (503 MB) are **gitignored** — never commit them.

```
cmu-final-project/
├── HANDOFF.md                      ← THIS FILE
├── .gitignore                      ← excludes data/, .venv/, root *.pdf, .Rhistory
├── .claude/launch.json             ← preview server config (python http.server on :8891)
├── Project_assignment_...pdf       ← course brief (gitignored)
└── project/
    ├── run_pipeline.sh             ← end-to-end runner (assumes data already downloaded)
    ├── README.md                   ← public-facing readme
    ├── .venv/                      ← Python venv (gitignored) — ALWAYS use this interpreter
    ├── data/
    │   ├── raw/                    ← downloaded data (gitignored, cached locally)
    │   └── processed/dataset.npz   ← model-ready arrays (gitignored)
    ├── src/                        ← all pipeline code (23 modules, numpy-first)
    ├── results/                    ← committed pipeline outputs (npz + json) — SOURCE OF TRUTH
    ├── figures/                    ← figure PNG+PDF (committed) and figures/web/*.jpg
    ├── manuscript/manuscript.md    ← full manuscript
    ├── docs/                       ← lit review, plan, one-pagers, CHANGES.md
    └── website/                    ← the interactive site (Vercel serves THIS folder)
        ├── index.html
        └── assets/{css,js,data,img}/
```

---

## 2. Environment — CRITICAL GOTCHAS

1. **Always use the project venv:** `project/.venv/bin/python` (Python 3.12.7, **numpy
   pinned to 1.26.4**). Do **NOT** use the system/Anaconda Python — pip-upgrading numpy to
   2.x there broke Anaconda's precompiled pandas. The venv has a mutually-compatible pinned
   stack.
   - venv packages: `numpy==1.26.4 scipy pandas matplotlib scikit-learn networkx POT ripser
     persim rasterio pyproj gudhi pillow`.
   - To recreate: `python3 -m venv project/.venv && project/.venv/bin/pip install
     numpy==1.26.4 scipy pandas matplotlib scikit-learn networkx POT ripser persim rasterio
     pyproj gudhi pillow`.
   - **One-line sanity check** (confirms venv + heavy deps in a single step):
     ```bash
     cd project/src && ../.venv/bin/python -c "import numpy,scipy,pandas,sklearn,ot,ripser,gudhi,rasterio; print('OK numpy', numpy.__version__)"
     ```
     Expect `OK numpy 1.26.4`. (`import ot` is the POT optimal-transport package.)

2. **Run scripts from `project/src/` using the relative interpreter path**, because scripts
   use relative paths via `config.py` (which resolves paths from its own location, so that's
   fine) — but the shell `cwd` matters for invoking the venv. Canonical invocation:
   ```bash
   cd project/src && ../.venv/bin/python <script>.py
   ```
   A frequent mistake is running from the repo root where `.venv/bin/python` doesn't exist
   (it's `project/.venv/...`). If you see `no such file or directory: .venv/bin/python`, you
   are in the wrong directory.

3. **`~/.config` on this Mac is owned by `root`** — regular tools can't write there. This
   broke `gh` (GitHub CLI). The workaround: a user-owned config dir at `~/.ghconfig`. For
   ALL `gh` commands you MUST set:
   ```bash
   export PATH="/opt/homebrew/bin:$PATH"          # gh is here (brew)
   export GH_CONFIG_DIR=~/.ghconfig               # gh auth token lives here
   ```
   `gh` is authenticated as GitHub account **oreopengguin** (token stored in keyring via the
   custom config dir). Plain `git push`/`pull` work normally (gh set up the credential
   helper).

---

## 3. The science (enough to defend it)

**Thesis:** Conflict = *moving mass meeting fixed human pressure*. Climate warming pushes
suitable habitat poleward/uphill; conflict emerges where that shift forces a species into
human-dominated land and the landscape can't route it around.

**Pipeline (each stage = one idea):**
1. **Habitat model (MaxEnt ≡ penalized Poisson point process).** Built from scratch. MaxEnt
   is the max-entropy Gibbs distribution `p(x) ∝ exp(β·f(x))` matching feature expectations
   at presences; it is *exactly* equivalent to an inhomogeneous Poisson point process
   (Renner & Warton 2013). Fit by **elastic-net-penalized Poisson likelihood via FISTA**
   (accelerated proximal gradient, soft-thresholding, backtracking). Features = MaxEnt
   classes: linear, quadratic, product, and hinge, with train-range **clamping** for honest
   future projection. Background = 70% **target-group** (cells where any of the 7 species
   was recorded → cancels shared observer bias) + 30% random land. Suitability output =
   cloglog `1−exp(−exp(η))`.
2. **Optimal transport (entropic Sinkhorn).** Treat present & future suitability as
   probability measures; solve `min_P ⟨P,C⟩ − εH(P)` (POT `ot.sinkhorn`) on a **coarsened
   grid** (factor cf=5, great-circle² cost) to get a barycentric **displacement field**
   `T(x)−x` and a **Wasserstein-2 range-shift** (km). *NOTE:* a single-Gaussian convolutional
   Sinkhorn was tried first and FAILED (collapsed to the domain centroid, gave nonsense
   southward shifts) — the coarse-grid explicit-cost approach is the correct one.
3. **Coexistence Friction** `F(x) = ⟨T(x), ∇H(x)⟩₊` — positive part of displacement dotted
   with the gradient of human modification `H`. High = habitat pushed *up* the human-pressure
   gradient = mechanistic conflict signal.
4. **Spectral connectivity (circuit theory).** Resistance `R = base + α(1−suit) + γH`;
   sparse graph Laplacian; solve `Lφ = b` with demand `b = present−future` (habitat lost
   sources current, gained sinks it). Node current = corridor intensity; local maxima =
   pinch-points. `current × H` = conflict corridors.
5. **Persistent homology (cubical, GUDHI).** Superlevel-set persistence of suitability;
   H0 = habitat patches, H1 = interior gaps. Fragmentation index + Wasserstein distance
   between present/future diagrams.
6. **Coexistence Risk Index (CRI)** = z(friction) + z(current·H) + z(suitability-gain-into-H).

**Study system:** 7 conflict-prone European mammals, GBIF occurrences, WorldClim climate,
Global Human Modification. Domain = Europe, bbox lon[-12,40] lat[34,72], grid 1/6° (≈18 km),
228×312 = 71,136 cells, **37,070 land cells**.

**The 7 species (order matters — used everywhere; colours are Okabe-Ito colourblind-safe):**
| key | common | colour | marker |
|---|---|---|---|
| Ursus arctos | Brown bear | #E69F00 | o |
| Canis lupus | Grey wolf | #CC79A7 | s |
| Lynx lynx | Eurasian lynx | #009E73 | ^ |
| Canis aureus | Golden jackal | #E6C200 | D |
| Sus scrofa | Wild boar | #0072B2 | P |
| Capreolus capreolus | Roe deer | #56B4E9 | v |
| Vulpes vulpes | Red fox | #D55E00 | X |

### Headline results (REAL — from `results/summary.json` & `robustness.json`)
- SDM spatial-block-CV **AUC 0.76–0.92** (mean 0.84), Boyce up to 0.99.
- Warming **+2.8 °C** (SSP2-4.5, 2081–2100); community-mean poleward shift **484 km**
  (per-species 364–615; all 7 northward).
- **Validation 1 (mechanism):** predicted vs observed range shift **Spearman ρ = 0.64**,
  Pearson r = 0.39 (n=7). 5/7 taxa observed poleward. **Grey wolf is the one outlier** —
  its recent range change is legal-protection-driven *recolonization* (Chapron et al. 2014),
  a known non-climate confound. Observed shifts come from splitting GBIF into a 1990–2007
  epoch (`occ_hist_*`) vs the recent `occ_*` records.
- **Validation 2 (interface):** Coexistence Friction predicts which human-dominated cells
  hold recent occurrences — standardized association 0.13, **permutation p = 0.0005**
  (4,618 interface cells).
- **Robustness:** SSP5-8.5 shifts bigger (mean **714 km**) but the *spatial* friction pattern
  is nearly identical (**r = 0.98**); grid-invariant (CV 0.5%); the from-scratch solver hits
  the maximum-entropy feature-matching constraint to **r = 0.99998**.
- Fragmentation H1 loops rise 2,389 → 2,536; CRI hotspots (verified vs `analysis.npz`) =
  **Alps** (strongest) + **Poland–Belarus lowland belt** + **NE-Baltic / Gulf-of-Finland**
  corner. Carpathians/Iberia/Fennoscandia are *not* leading hotspots; some coastal/island
  cells (esp. **Scotland**) are over-water friction **artefacts** — see `docs/CHANGES.md`.

---

## 4. Data acquisition — how & gotchas

All open, no institutional login, all downloadable from the terminal. Cached in
`project/data/raw/` (gitignored). To re-download:

- **GBIF occurrences** (`src/download_gbif.py`, `src/download_hist.py`): public
  `/occurrence/search` API, no auth. **CRITICAL GOTCHA: GBIF has a deep-pagination cliff —
  requests beyond offset 10,000 take ~12 s each (vs ~1 s below).** So each species is capped
  at **9,900 records** (`GBIF_MAX_RECORDS` in config). Also GBIF returns records
  **recency-first**, so the main `occ_*` files are ~2015–2026; a separate historical query
  (`download_hist.py`, year 1950–2009 → `occ_hist_*`) provides the past epoch for shift
  validation. Use small pages (limit=100), a ~0.2 s throttle, 3 worker threads. GBIF
  intermittently returns truncated JSON → the fetcher retries.
- **WorldClim 2.1** (curl): present bioclim `wc2.1_10m_bio.zip` + two futures
  `wc2.1_10m_bioc_MPI-ESM1-2-HR_ssp245_2081-2100.tif` and `...ssp585...` from
  `geodata.ucdavis.edu`. 10 arc-min. Predictors used = BIO 1,4,5,6,12,15,18,19.
- **Global Human Modification (gHM)** (figshare article 7283087, `gHM.zip`, 415 MB, global
  1 km, World Mollweide ESRI:54009). Reprojected/decimated to the grid in `io_utils.read_ghm`.

### Exact cold-download commands (if `data/raw/` is empty)
```bash
cd project/data/raw
# WorldClim present + two futures:
curl -sO "https://geodata.ucdavis.edu/climate/worldclim/2_1/base/wc2.1_10m_bio.zip"
curl -sO "https://geodata.ucdavis.edu/cmip6/10m/MPI-ESM1-2-HR/ssp245/wc2.1_10m_bioc_MPI-ESM1-2-HR_ssp245_2081-2100.tif"
curl -sO "https://geodata.ucdavis.edu/cmip6/10m/MPI-ESM1-2-HR/ssp585/wc2.1_10m_bioc_MPI-ESM1-2-HR_ssp585_2081-2100.tif"
# Global Human Modification (figshare) + unzip:
curl -sL -o gHM.zip "https://ndownloader.figshare.com/files/13448294" && unzip -o gHM.zip -d gHM_extracted
# GBIF occurrences (recent + historical) via the project scripts:
cd ../../src && ../.venv/bin/python download_gbif.py && ../.venv/bin/python download_hist.py
```
**Expected artifacts** (sanity of a complete download): `wc2.1_10m_bio.zip` (~48 MB), each
future `.tif` (~33 MB), `gHM.zip` (~415 MB), and **8 `occ_*.csv` + 7 `occ_hist_*.csv`**
(each recent species ≈8–10k rows; golden jackal fewer; `occ_ALL.csv` ≈58k rows). After
downloads, run the full pipeline: `cd project && ./run_pipeline.sh`.

---

## 5. Pipeline — modules & run order

Run everything (assumes `data/raw` populated): `cd project && ./run_pipeline.sh`.
Individual stages (`cd project/src && ../.venv/bin/python X.py`):

1. `config.py` — domain, grid, species list+colours+markers, predictors, constants. **Edit
   here to change species/palette/scenario.**
2. `io_utils.py` — builds the common grid; reads WorldClim (zip + multiband tif) and gHM
   (Mollweide→WGS84 reproject).
3. `download_gbif.py` / `download_hist.py` — occurrences (recent / historical).
4. `build_covariates.py` — stacks bioclim (present + ssp245 `Fz` + ssp585 `Fz585`),
   standardizes, spatial-thins to 1 presence/cell, builds target-group background →
   `data/processed/dataset.npz`.
5. `maxent_ppm.py` — the from-scratch model: `FeatureMaker`, `MaxentPPM` (FISTA solver),
   metrics (`auc_presence_background`, `boyce_index`, `tss_max`). **The mathematical core.**
6. `run_sdm.py` — fits per species, spatial block CV, predicts present/future(ssp245)/
   future585 suitability → `results/sdm.npz` + `sdm_metrics.json`.
7. `transport.py` — coarse-grid entropic OT, displacement field, Wasserstein km, friction.
8. `connectivity.py` — resistance surface, sparse Laplacian, current-flow, pinch score.
9. `topology.py` — cubical persistent homology (GUDHI), fragmentation index, diagram distance,
   persistence landscapes.
10. `risk.py` — CRI synthesis + validations (observed vs predicted shift, interface test).
11. `analysis.py` — orchestrates 7–10 across all species + community → `results/analysis.npz`
    + `summary.json`.
12. `robustness.py` — scenario (ssp245 vs 585), OT-reg & grid sensitivity, MaxEnt constraint
    check → `results/robustness.npz` + `robustness.json`.
13. `figstyle.py` — shared matplotlib style + colormaps (`SUIT`, `EMBER`, `FLOW`, `DIVSHIFT`,
    `HUMAN`) — all colourblind-safe (no red-green reliance).
14. `figdata.py` — figure loaders (analysis/summary/metrics/occ).
15. `fig1.py`…`fig4.py`, `figS1.py`, `figSDM.py` — the figures.
16. `export_web.py` — exports REAL data → `website/assets/data/*.json` + renders per-species
    SDM map PNGs + the risk map PNG + copies figure JPGs. **Run this after any figure/result
    change to update the website.**
17. `build_site.py` — LEGACY single-file HTML generator, **no longer the site source** (kept
    for reference). The live site is the hand-authored multi-file `website/`.

**Timing:** full pipeline ≈ a few minutes (SDM ~15 s, analysis ~26 s, robustness ~95 s).

---

## 6. Figures (all colourblind-safe; committed in `project/figures/`)

- `figure1_framework` — (a) occurrence density map, (b) climatic-niche PCA (Okabe-Ito +
  shape markers at centroids), (c) pipeline schematic, (d) skill dot-plot **AUC + Boyce
  only (TSS removed)**.
- `figure2_transport` — (a) bivariate present/future, (b) displacement streamlines, (c)
  poleward-shift hexbin + per-species trend lines (with shape markers), (d) friction map.
- `figure3_connectivity_topology` — (a) movement current, (b) conflict corridors + pinch
  points, (c) persistence diagram, (d) persistence landscapes.
- `figure4_risk_validation` — (a) CRI map + hotspot stars + cities, (b) predicted-vs-observed
  shift scatter (wolf outlier annotated, Spearman + Pearson), (c) friction–interface
  permutation null, (d) per-species risk heatmap.
- `figureS1_robustness` — (a) scenario dumbbell, (b) friction scenario-invariance scatter
  (r=0.98), (c) OT reg + grid sensitivity, (d) MaxEnt constraint check (r=0.99998).
- `figureSDM_present_future` — one map per species: filled present suitability, dashed 2090
  core outline, mean-displacement arrow. Uses a **per-species contrast stretch** ("relative
  suitability") for display only — see CHANGES.md.

**Colourblind approach:** Okabe-Ito categorical palette + **redundant marker shapes** so
colour is never the only channel. Sequential/diverging maps use perceptually-uniform,
red-green-safe colormaps. Documented in `docs/CHANGES.md`.

**TSS removal (important honesty note):** TSS was removed from Fig 1d and the website skill
chart because it needs a hard threshold + true absences (ill-suited to presence-only data).
The values still exist in `sdm_metrics.json` — they are just not displayed. Kept AUC + the
presence-only Boyce index. This is a documented reporting choice, NOT hiding a weak number.

---

## 7. Website — architecture (Vercel-hosted multi-file static app)

**Vercel setup:** repo is imported to Vercel; **Root Directory = `project/website`**;
framework preset = Other; no build command. Vercel **auto-redeploys on every push to
`main`**. The site is a plain static app (no framework, no build step). GitHub Pages was
retired (the old `gh-pages` branch was deleted).

**Files (`project/website/`):**
- `index.html` — all page sections. A complete HTML document (has `<head>`/`<title>`/emoji
  favicon). Sections in order: nav → hero (canvas field) → stat band → "the idea" →
  **01 Foundation** (Fig 1 + interactive niche chart + interactive skill chart + SDM viewer)
  → **02 Geometry** (Fig 2, Fig 3) → **Results** (6 stat tiles + 5 findings + Fig 4 + Fig S1)
  → **Significance** → **Frontiers** (future research cards) → **Conclusions** → **Game** →
  footer.
- `assets/css/style.css` — design system. Theme-aware via CSS custom properties on `:root`,
  redefined under `@media (prefers-color-scheme:dark)` and `:root[data-theme=dark|light]`.
  Fonts: serif (`Iowan Old Style`/Palatino/Georgia) + system sans + mono. Accent = ember
  `#c85a2b`. Has `.reveal` scroll-in, stat tiles, viz shells, SDM viewer, frontier cards.
- `assets/css/game.css` — all escape-room styles (progress, rooms, cards, keys, badges,
  confetti, door).
- `assets/js/main.js` — theme toggle (persisted in `localStorage` `goc-theme`), animated
  "poleward field" hero canvas, IntersectionObserver scroll-reveal, `window.GOC.tip`
  (shared tooltip) + `window.GOC.cssVar`.
- `assets/js/charts.js` — fetches `meta.json`, `skill.json`, `niche.json` (primary) then
  `fig2c.json`, `fig3b.json`, `fig4d.json`, `risk_grid.json` (secondary, loaded independently).
  Renders the **interactive niche SVG** (Gaussian-KDE **density contours matching Fig 1B** —
  polylines in `niche.json.species[*].contours`, level 0.4·max — + shape markers + toggle legend
  + hover **spotlight**), the **skill dot-plot**, the **6 future-research cards** (`FRONTIERS`
  array here), **and five data-driven figure recreations with element-specific hover**:
  `fig2c` (species shift-vs-latitude lines → species + shift@lat), `fig3b` (corridor map +
  16 pinch-point rings → rank + **place label** e.g. "near Warsaw, Poland" + intensity, + pixel-
  hover), `fig4a` (CRI map pixel-hover + **named bright-cluster labels** overlaid from
  `fig4a.json`), `fig4b` (predicted-vs-observed scatter → per-species values), `fig4d` (risk-
  decomposition heatmap → per-cell value + z). Sets `window.GOC.species` and fires
  `goc-data-ready`. Place/landmark/region names come from `src/geolabels.py` (public geographic
  facts, no download) — used only to annotate real committed coordinates.
- `assets/js/main.js` — theme toggle, hero flow-field, scroll-reveal, shared tooltip, **and**
  the interactive **pipeline strip** (`#pipeStrip`, hover/tap a stage), **stat count-up** on
  scroll, **nav scroll-spy**, and **figure panel-hover** (any `.figure[data-panels]` — hovering
  a quadrant of a 2×2 flagship figure highlights it and names the panel from its own title).
  All text is a rephrase of existing on-page copy. The top nav also has a **Sources** link
  (`sources.html`).
- `assets/js/maps.js` — the **present↔2090 SDM viewer**: drag divider to wipe, hover to read
  the real coarse suitability grid (`sdm_grids.json`, base64 Uint8 arrays), species chips, plus
  an **`▶ Auto-sweep`** toggle (`#sdmPlay`) that animates the wipe hands-free.
  Uses images `assets/img/sdm/<Species_key>_{present,future}.png` (key has spaces→underscores).
- `assets/js/game.js` — the escape-room game (see §8).
- `assets/data/*.json` — REAL exported data (from `export_web.py`). `meta.json` (species +
  key results), `skill.json`, `niche.json` (bioclim-PCA KDE density **contours**, Fig-1B-matched),
`fig2c.json` (per-species shift-vs-latitude lines), `fig3b.json` (corridor coarse grid + 16
pinch-point circles w/ `place` labels; paired with `img/corridor_map.png`), `fig4a.json`
(named CRI bright-cluster labels + extent), `fig4d.json` (per-species decomposition
matrix), `sdm_grids.json` (coarse suitability
  for hover, base64), `risk_grid.json` (coarse CRI).
- `assets/img/` — figure JPGs, `risk_map.png` (clean CRI map for the game), `sdm/*.png`.

**Data flow (end to end):**
```
 data/raw/ (GBIF, WorldClim, gHM)          [downloaded, gitignored]
      │  build_covariates.py
      ▼
 data/processed/dataset.npz                [model-ready arrays, gitignored]
      │  run_sdm.py (MaxEnt/PPP + spatial CV)
      ▼
 results/sdm.npz, sdm_metrics.json
      │  analysis.py (transport → connectivity → topology → risk) + robustness.py
      ▼
 results/analysis.npz, summary.json, robustness.json   ← SOURCE OF TRUTH (committed)
      │  figN.py / figS1.py / figSDM.py        │  export_web.py
      ▼                                        ▼
 figures/*.png,*.pdf  ──►  figures/web/*.jpg   website/assets/data/*.json + assets/img/*
                                               │  (JS fetch() at runtime)
                                               ▼
                                     website/index.html + assets/js/*  ──► Vercel
```
**To refresh site data after a science change: re-run the affected `figN.py` → then
`export_web.py` → commit → push.** `export_web.py` reads the committed `results/*` **plus**
`data/processed/dataset.npz` (the niche-PCA panel needs the standardized predictors).
⚠ **`dataset.npz` is gitignored**, so on a *fresh clone* you must regenerate it first
(download data → `build_covariates.py`) before `export_web.py` will run — it is a
deterministic product, and the website's numbers still trace to the committed `results/*`.
Locally on this machine `dataset.npz` already exists, so `export_web.py` runs directly.

**Local preview & inspection loop:** `.claude/launch.json` defines a launch config
**named `coexistence-site`** (pass this name to `preview_start`) that runs
`python3 -m http.server 8891 --directory project/website`. Note this preview server
**intentionally uses system `python3`, not the venv** — it only serves static files, so no
project dependencies are needed (this is not a violation of the "always use the venv" rule,
which applies to running pipeline code). Use the Claude_Preview MCP tools (`preview_start`
with name `coexistence-site`, then `preview_screenshot`, `preview_eval`,
`preview_console_logs`) to render and inspect. Or plainly `curl http://localhost:8891/`.
Always do a build→render→critique→fix loop; check both themes and mobile.

---

## 8. The escape-room game (`assets/js/game.js`)

Title: *"Escape Room: Save the Wildlife Before It's Too Late."* Right after Conclusions.
Four "research stations", each teaching one pipeline idea; collect 4 keys → final unlock.

- **Room 1 — Restore the Pipeline:** reorder 4 cards into
  `Climate Data → Habitat Model → Animal Movement → Coexistence Risk Map`. Drag is a
  **pointer-based live sortable** (cards re-flow as you drag, held card tracks the cursor with
  no drop-shadow; absolute layout via a `--ty` CSS var). A grip handle keeps touch-scroll
  working; ▲▼ buttons + arrow keys are the accessible fallback.
- **Wrong-answer feedback (all rooms):** a compact red ✕ + a message from a large rotating
  pool (`WRONG_MSGS`) appears next to the check/submit button via `showWrong()`; consecutive
  wrong guesses always change. The verbose green box is reserved for correct answers.
- **Room 2 — Predict the Migration:** 4 direction buttons; correct = **North**; animates a
  compass arrow north.
- **Room 3 — Spot the Conflict Zones:** multi-select; correct = **Farmland + City**. Guarded
  by a per-room `locked` flag so re-submitting the correct answer can't double-log the note or
  double-add the Next button (`awardKey` is also idempotent).
- **Room 4 — Find the Future Hotspots:** click inside any of three **accept-regions** on
  `risk_map.png` — `REGIONS` boxes for the **Alps**, the **NE Baltic / Gulf-of-Finland**
  corner, and the **Poland–Belarus belt** (the genuinely-bright CRI clusters, verified against
  `analysis.npz`). Clicking **Scotland** (`SCOTLAND` box) shows the over-water-friction
  **artefact explanation** (rotating `SCOTLAND_MSGS`) and does not penalise; clicking an
  already-found region shows a rotating neutral "already found" message (`ALREADY_MSGS`, via
  `showAlready()`); a genuine miss shows the red ✕ (`showWrong()`). Map extent `[-12,40,34,72]`.
- **Final:** 4 keys fly into a lock, door opens, confetti, 4 badges, star rating, "Explore
  the Project Again" (scroll to top) + "Play again".

**Extra features added (beyond spec):** per-room **hint** button, a **field notebook** that
logs the real fact learned each room, **star score** (5 − penalty from wrong attempts +
hints), **session-persistent progress** (`sessionStorage` `goc-game`), full **keyboard +
touch** support, **play-again/restart**. All facts mirror the site — **no new science
introduced**. Every room fully tested end-to-end via preview_eval.

**To modify the game:** it's one self-contained IIFE with a room router (`render()`), helper
`h()` (element builder), `state` object, and per-room functions `room1..room4` + `finalScreen`.
`NOTES[]` = notebook facts; `HOTSPOTS[]` = room-4 targets; `FRONTIERS[]` is in charts.js.

---

## 9. Git, GitHub & Vercel — operational

- **Repo:** `github.com/oreopengguin/cmu-wildlife-conflict` (currently **public**, so Vercel
  free Pages/deploys work). Owner account: **oreopengguin**, git identity `Zack
  <xz.zhang21@gmail.com>` (maps to oreopengguin).
- **Contributor policy (STRICT):** the owner wants to be the **only** contributor. **Do NOT
  add `Co-Authored-By` trailers** to commits. (Earlier commits that had one were history-
  rewritten to remove it and force-pushed.) Verify after committing:
  `git log --all --pretty='%an %B' | grep -i "claude\|anthropic\|co-authored"` → must be empty.
- **Commit/push (with the gh workaround):**
  ```bash
  cd /Users/zacharyzhang/cmu-final-project
  export PATH="/opt/homebrew/bin:$PATH"; export GH_CONFIG_DIR=~/.ghconfig
  git add -A && git commit -m "..."      # NO co-author trailer
  git push origin main                    # Vercel auto-redeploys (~30–60 s)
  ```
- **Verify deploy:** `curl -s -o /dev/null -w "%{http_code}" https://cmu-wildlife-conflict.vercel.app/`
  and check a new asset resolves (200).
- **Never commit** `project/data/` or `project/.venv/` (both gitignored).

---

## 10. Key decisions & rationale (so you don't relitigate them)

- **From-scratch MaxEnt as penalized PPP via FISTA** — the "algorithmic wizardry" the owner
  wanted; verified correct (constraint check r=0.99998).
- **Coarse-grid OT, not convolutional Sinkhorn** — the convolutional version failed
  (centroid collapse, southward nonsense). Coarse grid (cf=5) + explicit great-circle cost +
  `ot.sinkhorn` (reg=0.02) gives correct poleward shifts. Do NOT switch to
  `sinkhorn_stabilized` (it returned degenerate W=0 plans here).
- **Wolf outlier is real and honest** — recolonization confound; keep it visible, don't hide.
- **Both validations are modest but real** — ρ=0.64 and p=0.0005. Do not overclaim. The
  framework is a *methods* contribution; the honest framing is "strong computational-ecology
  methods paper," not a guaranteed Nature paper.
- **TSS removed with justification** (see §6).
- **Per-species display stretch** on maps is labelled and documented — display only.

---

## 11. Common tasks / how to continue

- **Change the species set or colours:** edit `SPECIES` + `SPECIES_MARKER` in `config.py`,
  re-run the whole pipeline (`run_pipeline.sh`), then `export_web.py`, commit, push.
- **Regenerate one figure:** `cd project/src && ../.venv/bin/python figN.py`, then re-run
  `export_web.py` to push the web JPG + data, commit, push.
- **Edit website copy/layout:** edit `website/index.html` / `assets/css/*` / `assets/js/*`
  directly (no build step), preview locally, commit, push.
- **Edit the game:** `assets/js/game.js` (+ `game.css`). Keep it completable by a
  10-min-presentation audience and introduce **no new science**.
- **Add a future-research card:** append to `FRONTIERS[]` in `charts.js` (keep it grounded in
  existing project concepts + add a plain-language line).
- **After ANY change that affects results/figures:** update `docs/CHANGES.md` and this
  HANDOFF.md.

---

## 12. Documents to read for depth
- `project/manuscript/manuscript.md` — full paper (abstract, methods, results, discussion).
- `project/docs/01_literature_review.md` — 50+ annotated references.
- `project/docs/02_research_plan.md` — methodology & novelty.
- `project/docs/CHANGES.md` — every change to how results are presented (honesty log).
- `project/docs/ONE_PAGER_for_teammates.md` — plain-language project explainer.
- `project/docs/WEBSITE_OVERHAUL_ONEPAGER.md` — plain-language website/game explainer.
- `project/README.md` — public readme with the reproduce recipe + results table.

---

## 13. TROUBLESHOOTING (symptom → cause → fix)

| Symptom | Cause | Fix |
|---|---|---|
| `no such file or directory: .venv/bin/python` | Running from repo root; venv is under `project/` | `cd project/src && ../.venv/bin/python …` |
| `numpy.core.multiarray failed to import` / pandas import crash | Using system/Anaconda Python (numpy 2.x vs precompiled pandas) | Use `project/.venv/bin/python` only |
| `gh: ... mkdir /Users/…/.config/gh: permission denied` or "not logged in" | `~/.config` is root-owned | `export GH_CONFIG_DIR=~/.ghconfig` (+ `PATH=/opt/homebrew/bin`); token already stored there |
| GBIF download stalls ~offset 9000–10000 | GBIF deep-pagination cliff (>10k offset ≈12 s/page) | Keep `GBIF_MAX_RECORDS=9900`; don't raise it |
| GBIF "Expecting ':' delimiter" JSON errors | GBIF intermittently truncates responses | Fetcher already retries; use small pages (limit 100) + throttle |
| OT gives huge/**southward** shifts (e.g. −55°, W≈0) | Wrong OT method (convolutional or `sinkhorn_stabilized`) | Use coarse-grid `ot.sinkhorn` (reg≈0.02, cf=5) as in `transport.py` — do NOT change it |
| Validation shift correlation is only moderate (ρ≈0.64) | Real — wolf recolonization confound + opportunistic GBIF | This is correct/honest; keep the wolf outlier visible, do not "fix" it |
| SDM maps render nearly all-dark | cloglog suitability concentrated at low values | Per-species 98th-pct contrast stretch (already applied; labelled "relative suitability") |
| A `→`/`⇄` glyph renders as a box in a figure | Font lacks the glyph | Use mathtext (`$\rightarrow$`) or ASCII in matplotlib text |
| Website shows old content after push | Vercel cache / not yet redeployed | Wait ~30–60 s; `curl` the URL; hard-refresh |
| `export_web.py` fails on a fresh clone (`dataset.npz` not found) | It reads gitignored `data/processed/dataset.npz` (niche PCA) | Regenerate it first: download data (§4) → `build_covariates.py` |
| Figure colours look wrong for a colourblind reviewer | — | Palette is Okabe-Ito + shape markers already; keep both channels (see `docs/CHANGES.md`) |

## 14. ROADMAP — what's done, what's open, what's next

**Done & shipped:** full pipeline; 6 figures; manuscript; interactive website + escape-room
game on Vercel; two one-pagers; lit review; research plan; CHANGES log; this handoff +
`verify.sh`.

**Deliberately NOT done (open decisions a successor may take up):**
- The manuscript is a Markdown draft; it has **not** been typeset (LaTeX/Word) or submitted.
  Honest venue framing = strong computational-ecology *methods* paper (Methods in Ecology &
  Evolution / Ecography), not a guaranteed Nature paper. Don't oversell it.
- Only one climate model (MPI-ESM1-2-HR) is used; a **multi-GCM ensemble** would strengthen
  robustness (currently only 2 SSP scenarios of one GCM).
- Resolution is coarse (~18 km). A **fine-resolution downscale** to one region is listed as a
  future-research idea (see the `FRONTIERS[]` array in `website/assets/js/charts.js`).
- The 6 **future-research ideas** on the site are proposals, not implemented.
- No independent **conflict dataset** was found that's openly downloadable + pan-European; the
  friction→interface test uses occurrence-in-human-cells as the interface proxy. A real
  conflict dataset would be the strongest possible Validation 2 upgrade.

**If asked to "extend the science":** the cleanest high-value next steps are (a) a multi-GCM
ensemble mean of the friction field, (b) Gromov–Wasserstein coupled predator–prey transport,
or (c) implementing the "inverse transport / stepping-stone reserve placement" frontier idea.
All fit the existing `transport.py` machinery.

## 15. MAINTENANCE CHECKLIST (do this for every future change)
1. Make the change; keep everything grounded in real pipeline output.
2. If figures/results/presentation changed → update `project/docs/CHANGES.md`.
3. If the site data/images are affected → re-run `export_web.py`.
4. Preview locally (both themes + mobile), critique, fix.
5. **Run `bash verify.sh` — it must print 0 failed** before you commit.
6. Commit **without** a `Co-Authored-By` trailer; push to `main`; confirm Vercel redeployed.
7. **Update THIS file (`HANDOFF.md`)** — the status line, any new files/decisions/gotchas —
   and extend `verify.sh` if you added assets it should check.
