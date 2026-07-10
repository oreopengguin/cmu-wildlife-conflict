"""
Global configuration for the "Geometry of Coexistence" project.

Everything downstream imports the study domain, grid, species list, and paths
from here so the whole pipeline stays consistent.
"""
from __future__ import annotations
import os
from pathlib import Path

# ----------------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]          # .../project
DATA_RAW = ROOT / "data" / "raw"
DATA_PROC = ROOT / "data" / "processed"
RESULTS = ROOT / "results"
FIGDIR = ROOT / "figures"
for _p in (DATA_RAW, DATA_PROC, RESULTS, FIGDIR):
    _p.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------------
# Study domain: continental Europe (well-sampled; documented carnivore recovery)
# ----------------------------------------------------------------------------
# lon_min, lon_max, lat_min, lat_max
BBOX = (-12.0, 40.0, 34.0, 72.0)
LON_MIN, LON_MAX, LAT_MIN, LAT_MAX = BBOX

# Analysis grid resolution in degrees. WorldClim 10 arc-min = 1/6 deg.
GRID_RES = 1.0 / 6.0            # ~18 km at the equator

# ----------------------------------------------------------------------------
# Species: conflict-prone European large/meso mammals with dense GBIF records
# and active range dynamics. Keys are GBIF usageKeys resolved at download time.
# ----------------------------------------------------------------------------
# Colours: Okabe-Ito colourblind-safe qualitative palette (distinguishable
# under deuteranopia/protanopia/tritanopia). Paired with redundant marker
# shapes in figures so colour is never the sole channel.
SPECIES = [
    ("Ursus arctos",        "Brown bear",     "#E69F00"),  # orange
    ("Canis lupus",         "Grey wolf",      "#CC79A7"),  # reddish purple
    ("Lynx lynx",           "Eurasian lynx",  "#009E73"),  # bluish green
    ("Canis aureus",        "Golden jackal",  "#E6C200"),  # gold
    ("Sus scrofa",          "Wild boar",      "#0072B2"),  # blue
    ("Capreolus capreolus", "Roe deer",       "#56B4E9"),  # sky blue
    ("Vulpes vulpes",       "Red fox",        "#D55E00"),  # vermilion
]
# Redundant marker per species (shape encoding, colourblind backup)
SPECIES_MARKER = {
    "Ursus arctos": "o", "Canis lupus": "s", "Lynx lynx": "^",
    "Canis aureus": "D", "Sus scrofa": "P", "Capreolus capreolus": "v",
    "Vulpes vulpes": "X",
}
SPECIES_NAMES = [s[0] for s in SPECIES]
SPECIES_COMMON = {s[0]: s[1] for s in SPECIES}
SPECIES_COLOR = {s[0]: s[2] for s in SPECIES}

# Bioclim variable metadata (WorldClim BIO1..BIO19)
BIOCLIM_LABELS = {
    1: "Annual Mean Temp", 2: "Mean Diurnal Range", 3: "Isothermality",
    4: "Temp Seasonality", 5: "Max Temp Warmest Mo", 6: "Min Temp Coldest Mo",
    7: "Temp Annual Range", 8: "Mean Temp Wettest Qtr", 9: "Mean Temp Driest Qtr",
    10: "Mean Temp Warmest Qtr", 11: "Mean Temp Coldest Qtr", 12: "Annual Precip",
    13: "Precip Wettest Mo", 14: "Precip Driest Mo", 15: "Precip Seasonality",
    16: "Precip Wettest Qtr", 17: "Precip Driest Qtr", 18: "Precip Warmest Qtr",
    19: "Precip Coldest Qtr",
}
# Predictor subset used for the SDM (reduce collinearity; ecologically core set)
PREDICTORS = [1, 4, 5, 6, 12, 15, 18, 19]

# Occurrence download settings
GBIF_MAX_RECORDS = 9900       # hard cap per species (paged); thinning follows
GBIF_PAGE = 100                # small pages => reliable, non-truncated responses
OCC_YEAR_MIN = 1990            # modern records only

# Optimal transport
SINKHORN_EPS = 0.02            # entropic regularization (tuned in analysis)
SINKHORN_ITERS = 2000

RANDOM_SEED = 20260708

# Future climate scenario used for the headline analysis
SCENARIO = "ssp245"
SCENARIO_LABEL = "SSP2-4.5 (2081-2100)"
