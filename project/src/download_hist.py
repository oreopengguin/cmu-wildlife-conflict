"""
Fetch a HISTORICAL epoch (1990-2009) of occurrences per species, so the
observed range shift (historical -> recent) can validate the OT prediction.
Uses the same robust paged fetch, filtered to old years.
"""
from __future__ import annotations
import time, urllib.parse
import pandas as pd
import config as C
from download_gbif import _get, match_key, API
from concurrent.futures import ThreadPoolExecutor


def hist_species(name):
    key = match_key(name)
    base = {
        "taxonKey": key, "hasCoordinate": "true", "hasGeospatialIssue": "false",
        "decimalLatitude": f"{C.LAT_MIN},{C.LAT_MAX}",
        "decimalLongitude": f"{C.LON_MIN},{C.LON_MAX}",
        "year": "1950,2009", "limit": 100,
    }
    cnt = _get(f"{API}/occurrence/search?{urllib.parse.urlencode({**base,'limit':0})}")["count"]
    target = min(cnt, 9900)
    print(f"  [hist] {name}: {cnt} historical records, fetching {target}", flush=True)
    rows, offset, fails = [], 0, 0
    while offset < target and offset < 9900:
        q = urllib.parse.urlencode({**base, "offset": offset})
        d = _get(f"{API}/occurrence/search?{q}")
        if d is None:
            fails += 1; offset += 100
            if fails > 20:
                break
            continue
        res = d.get("results", [])
        if not res:
            break
        for o in res:
            unc = o.get("coordinateUncertaintyInMeters")
            if unc is not None and unc > 20000:
                continue
            rows.append({"species": name, "lon": o.get("decimalLongitude"),
                         "lat": o.get("decimalLatitude"), "year": o.get("year")})
        offset += 100
        time.sleep(0.2)
    df = pd.DataFrame(rows).dropna(subset=["lon", "lat"])
    df.to_csv(C.DATA_RAW / f"occ_hist_{name.replace(' ', '_')}.csv", index=False)
    print(f"  [hist] DONE {name}: {len(df)} historical records", flush=True)
    return df


def main():
    with ThreadPoolExecutor(max_workers=3) as ex:
        list(ex.map(hist_species, C.SPECIES_NAMES))
    print("[hist] all done")


if __name__ == "__main__":
    main()
