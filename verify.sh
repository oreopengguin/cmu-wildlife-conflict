#!/usr/bin/env bash
# ============================================================================
# verify.sh — executable handoff check for "The Geometry of Coexistence".
# Run from the repo root:  bash verify.sh
# Confirms the environment, data-of-record, website assets, reproducibility,
# git hygiene, and that the site serves — so a successor KNOWS (not hopes) the
# project is in a workable state. Non-destructive (restores anything it touches).
# ============================================================================
set -uo pipefail
cd "$(dirname "$0")"
ROOT="$(pwd)"
PY="project/.venv/bin/python"
pass=0; fail=0
ok(){ printf "  \033[32m✓\033[0m %s\n" "$1"; pass=$((pass+1)); }
no(){ printf "  \033[31m✗\033[0m %s\n" "$1"; fail=$((fail+1)); }
hdr(){ printf "\n\033[1m%s\033[0m\n" "$1"; }

hdr "1. Python environment"
if [ -x "$PY" ]; then ok "venv interpreter exists ($PY)"; else no "venv missing — see HANDOFF.md §2"; fi
if "$PY" -c "import numpy,scipy,pandas,sklearn,ot,ripser,gudhi,rasterio,matplotlib,networkx,persim,pyproj" 2>/dev/null; then
  ok "all pipeline deps import"; else no "a dependency failed to import"; fi
NPV=$("$PY" -c "import numpy;print(numpy.__version__)" 2>/dev/null || echo "?")
[ "$NPV" = "1.26.4" ] && ok "numpy pinned correctly ($NPV)" || no "numpy is $NPV, expected 1.26.4"

hdr "2. Results of record (committed source of truth)"
for f in results/sdm.npz results/analysis.npz results/summary.json results/robustness.json results/sdm_metrics.json; do
  [ -s "project/$f" ] && ok "$f present" || no "$f MISSING"
done

hdr "3. Website assets"
for f in index.html assets/css/style.css assets/css/game.css \
         assets/js/main.js assets/js/charts.js assets/js/maps.js assets/js/game.js \
         assets/data/meta.json assets/data/skill.json assets/data/niche.json \
         assets/data/sdm_grids.json assets/data/risk_grid.json assets/img/risk_map.png \
         assets/data/fig2c.json assets/data/fig3b.json assets/data/fig4d.json \
         assets/img/corridor_map.png sources.html; do
  [ -s "project/website/$f" ] && ok "$f" || no "$f MISSING"
done
NSDM=$(ls project/website/assets/img/sdm/*.png 2>/dev/null | wc -l | tr -d ' ')
[ "$NSDM" = "14" ] && ok "14 per-species SDM map images" || no "expected 14 SDM images, found $NSDM"

hdr "4. Figures"
for n in figure1_framework figure2_transport figure3_connectivity_topology \
         figure4_risk_validation figureS1_robustness figureSDM_present_future; do
  [ -s "project/figures/$n.png" ] && ok "$n.png" || no "$n.png MISSING"
done

hdr "5. Reproducibility (regenerate one figure, then restore)"
if [ -x "$PY" ]; then
  if ( cd project/src && ../.venv/bin/python figSDM.py 2>/dev/null | grep -q "saved figureSDM" ); then
    ok "figSDM.py regenerates successfully"
  else no "figSDM.py failed to regenerate"; fi
  git checkout -- project/figures/figureSDM_present_future.png project/figures/figureSDM_present_future.pdf 2>/dev/null
else no "skipped (no venv)"; fi

hdr "6. Git hygiene"
if git log --all --pretty='%an %B' 2>/dev/null | grep -qi "claude\|anthropic\|co-authored"; then
  no "co-author trailer / Claude reference found in history (must be sole contributor)"
else ok "no co-author trailer anywhere in history"; fi
git ls-files --error-unmatch HANDOFF.md >/dev/null 2>&1 && ok "HANDOFF.md is committed" || no "HANDOFF.md not committed"
if git ls-files | grep -qE "project/data/|project/\.venv/"; then no "data/ or .venv/ leaked into git"; else ok "data/ and .venv/ correctly gitignored"; fi

hdr "7. Site serves (smoke test on :8899)"
if [ -x "$(command -v python3)" ]; then
  ( cd project/website && python3 -m http.server 8899 >/dev/null 2>&1 & echo $! > /tmp/goc_verify.pid )
  sleep 1.2
  CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8899/ 2>/dev/null || echo 000)
  TITLE=$(curl -s http://localhost:8899/ 2>/dev/null | grep -o "<title>[^<]*</title>" | head -1)
  META=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8899/assets/data/meta.json 2>/dev/null || echo 000)
  kill "$(cat /tmp/goc_verify.pid)" 2>/dev/null; rm -f /tmp/goc_verify.pid
  [ "$CODE" = "200" ] && ok "index served (HTTP 200) $TITLE" || no "index did not serve (HTTP $CODE)"
  [ "$META" = "200" ] && ok "data JSON served (HTTP 200)" || no "meta.json did not serve (HTTP $META)"
else no "python3 not found for smoke test"; fi

hdr "8. Live deployment (optional; needs network)"
LIVE=$(curl -s -m 8 -o /dev/null -w "%{http_code}" https://cmu-wildlife-conflict.vercel.app/ 2>/dev/null || echo 000)
[ "$LIVE" = "200" ] && ok "Vercel site live (HTTP 200)" || printf "  \033[33m∼\033[0m Vercel check skipped/unreachable (HTTP %s) — not a failure offline\n" "$LIVE"

printf "\n\033[1m==== %d passed, %d failed ====\033[0m\n" "$pass" "$fail"
[ "$fail" -eq 0 ] && { echo "Environment is healthy — safe to continue. See HANDOFF.md."; exit 0; } || \
  { echo "Some checks failed — read the ✗ lines and HANDOFF.md before proceeding."; exit 1; }
