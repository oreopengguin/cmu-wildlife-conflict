#!/usr/bin/env bash
# End-to-end pipeline for "The Geometry of Coexistence".
# Assumes data already downloaded into data/raw (climate, gHM, occurrences).
set -euo pipefail
cd "$(dirname "$0")"
PY=.venv/bin/python
cd src
echo "=== [1/6] build covariates ==="; $PY build_covariates.py
echo "=== [2/6] fit SDMs (MaxEnt/PPP) ==="; $PY run_sdm.py
echo "=== [3/6] geometric analysis (OT/graph/TDA/risk) ==="; $PY analysis.py
echo "=== [4/7] robustness + scenario sensitivity ==="; $PY robustness.py
echo "=== [5/7] main figures 1-4 ==="; $PY fig1.py && $PY fig2.py && $PY fig3.py && $PY fig4.py
echo "=== [6/7] supplementary figure S1 ==="; $PY figS1.py
echo "=== [7/7] build website ==="; $PY build_site.py
echo "=== DONE. figures in project/figures, site in project/website ==="
ls -lh ../figures
