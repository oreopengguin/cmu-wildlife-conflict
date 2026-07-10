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
echo "=== [4/8] robustness + scenario sensitivity ==="; $PY robustness.py
echo "=== [5/8] main figures 1-4 ==="; $PY fig1.py && $PY fig2.py && $PY fig3.py && $PY fig4.py
echo "=== [6/8] supplementary figures (S1, SDM present/future) ==="; $PY figS1.py && $PY figSDM.py
echo "=== [7/8] web-res figure JPGs ==="; $PY - <<'PYIMG'
from PIL import Image; import os
os.makedirs('../figures/web', exist_ok=True)
for n in ['figure1_framework','figure2_transport','figure3_connectivity_topology','figure4_risk_validation','figureS1_robustness','figureSDM_present_future']:
    im=Image.open(f'../figures/{n}.png').convert('RGB'); w,h=im.size
    im.resize((1600,int(h*1600/w)), Image.LANCZOS).save(f'../figures/web/{n}.jpg', quality=88, optimize=True)
PYIMG
echo "=== [8/8] export interactive website data + images ==="; $PY export_web.py
echo "=== DONE. figures in project/figures, interactive site in project/website ==="
ls -lh ../figures
