"""
Download GBIF occurrence records for the study species over the European domain.

Uses the public /occurrence/search endpoint (no authentication). We page through
records, keep only georeferenced, low-uncertainty, modern records, and cache a
tidy CSV per species plus a combined file used later for target-group background.
"""
from __future__ import annotations
import sys, time, json, urllib.parse, urllib.request
import pandas as pd
import config as C

API = "https://api.gbif.org/v1"


def _get(url: str, tries: int = 6):
    """Robust GET. Reads the full body (handles slow/partial streams) and
    retries on truncated-JSON errors, which GBIF emits intermittently."""
    req = urllib.request.Request(url, headers={"Accept-Encoding": "identity"})
    for k in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                buf = b""
                while True:
                    chunk = r.read(65536)
                    if not chunk:
                        break
                    buf += chunk
                return json.loads(buf.decode("utf-8"))
        except Exception as e:
            if k == tries - 1:
                print(f"    ! page failed after {tries} tries: {type(e).__name__}", flush=True)
                return None
            time.sleep(0.6 * (k + 1))
    return None


def match_key(name: str) -> int:
    q = urllib.parse.urlencode({"name": name})
    d = _get(f"{API}/species/match?{q}")
    key = d.get("usageKey")
    print(f"  matched {name!r} -> usageKey {key} ({d.get('scientificName')})")
    return key


def download_species(name: str) -> pd.DataFrame:
    key = match_key(name)
    lon = f"{C.LON_MIN},{C.LON_MAX}"
    lat = f"{C.LAT_MIN},{C.LAT_MAX}"
    base = {
        "taxonKey": key,
        "hasCoordinate": "true",
        "hasGeospatialIssue": "false",
        "decimalLatitude": lat,
        "decimalLongitude": lon,
        "year": f"{C.OCC_YEAR_MIN},2026",
        "limit": C.GBIF_PAGE,
    }
    # total count
    cnt = _get(f"{API}/occurrence/search?{urllib.parse.urlencode({**base,'limit':0})}")["count"]
    target = min(cnt, C.GBIF_MAX_RECORDS)
    print(f"  {name}: {cnt} records available, fetching up to {target}")
    rows, offset, fails = [], 0, 0
    while offset < target and offset < 100000:  # API hard offset limit
        q = urllib.parse.urlencode({**base, "offset": offset})
        d = _get(f"{API}/occurrence/search?{q}")
        if d is None:
            fails += 1
            offset += C.GBIF_PAGE
            if fails > 20:
                print(f"    too many failures, stopping {name} at offset {offset}", flush=True)
                break
            continue
        res = d.get("results", [])
        if not res:
            break
        for o in res:
            unc = o.get("coordinateUncertaintyInMeters")
            if unc is not None and unc > 20000:      # drop very coarse records
                continue
            rows.append({
                "species": name,
                "lon": o.get("decimalLongitude"),
                "lat": o.get("decimalLatitude"),
                "year": o.get("year"),
                "basis": o.get("basisOfRecord"),
                "uncertainty_m": unc,
            })
        offset += C.GBIF_PAGE
        time.sleep(0.20)                     # polite throttle -> avoid 429s
        if offset % 3000 == 0:
            print(f"    ... {name}: {offset}/{target}", flush=True)
    df = pd.DataFrame(rows).dropna(subset=["lon", "lat"])
    print(f"  {name}: kept {len(df)} clean records")
    return df


def _one(name):
    print(f"[GBIF] start {name}", flush=True)
    df = download_species(name)
    out = C.DATA_RAW / f"occ_{name.replace(' ', '_')}.csv"
    df.to_csv(out, index=False)
    print(f"[GBIF] DONE {name}: {len(df)} -> {out.name}", flush=True)
    return df


def main():
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=3) as ex:
        all_frames = list(ex.map(_one, C.SPECIES_NAMES))
    combined = pd.concat(all_frames, ignore_index=True)
    combined.to_csv(C.DATA_RAW / "occ_ALL.csv", index=False)
    print(f"[GBIF] combined {len(combined)} records across {len(all_frames)} species")
    # quick summary
    print(combined.groupby("species").size())


if __name__ == "__main__":
    main()
