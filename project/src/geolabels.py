"""
Honest geographic labelling for the interactive maps.

Nothing here is pipeline output — these are public geographic facts (well-known
city coordinates, country bounding boxes, a few named physical regions) used to
*annotate* real, committed coordinates (pinch-points, risk hotspots). No data is
downloaded and nothing requires an institutional login.
"""
from __future__ import annotations
import math

# (lat, lon, name, country) — well-known European cities (capitals + major metros).
CITIES = [
    (51.51, -0.13, "London", "UK"), (48.85, 2.35, "Paris", "France"),
    (52.52, 13.40, "Berlin", "Germany"), (40.42, -3.70, "Madrid", "Spain"),
    (41.90, 12.50, "Rome", "Italy"), (52.23, 21.01, "Warsaw", "Poland"),
    (48.21, 16.37, "Vienna", "Austria"), (52.37, 4.90, "Amsterdam", "Netherlands"),
    (50.85, 4.35, "Brussels", "Belgium"), (50.45, 30.52, "Kyiv", "Ukraine"),
    (55.75, 37.62, "Moscow", "Russia"), (59.94, 30.31, "Saint Petersburg", "Russia"),
    (53.90, 27.57, "Minsk", "Belarus"), (50.08, 14.44, "Prague", "Czechia"),
    (47.50, 19.04, "Budapest", "Hungary"), (44.43, 26.10, "Bucharest", "Romania"),
    (42.70, 23.32, "Sofia", "Bulgaria"), (37.98, 23.73, "Athens", "Greece"),
    (41.01, 28.98, "Istanbul", "Türkiye"), (39.93, 32.86, "Ankara", "Türkiye"),
    (59.33, 18.07, "Stockholm", "Sweden"), (59.91, 10.75, "Oslo", "Norway"),
    (55.68, 12.57, "Copenhagen", "Denmark"), (60.17, 24.94, "Helsinki", "Finland"),
    (56.95, 24.11, "Riga", "Latvia"), (54.69, 25.28, "Vilnius", "Lithuania"),
    (59.44, 24.75, "Tallinn", "Estonia"), (53.35, -6.26, "Dublin", "Ireland"),
    (38.72, -9.14, "Lisbon", "Portugal"), (47.37, 8.54, "Zurich", "Switzerland"),
    (46.20, 6.14, "Geneva", "Switzerland"), (45.46, 9.19, "Milan", "Italy"),
    (48.14, 11.58, "Munich", "Germany"), (53.55, 9.99, "Hamburg", "Germany"),
    (50.11, 8.68, "Frankfurt", "Germany"), (45.81, 15.98, "Zagreb", "Croatia"),
    (44.79, 20.45, "Belgrade", "Serbia"), (50.06, 19.94, "Kraków", "Poland"),
    (54.35, 18.65, "Gdańsk", "Poland"), (51.11, 17.04, "Wrocław", "Poland"),
    (52.41, 16.93, "Poznań", "Poland"), (53.13, 23.16, "Białystok", "Poland"),
    (51.25, 22.57, "Lublin", "Poland"), (53.78, 20.49, "Olsztyn", "Poland"),
    (49.84, 24.03, "Lviv", "Ukraine"), (46.48, 30.72, "Odesa", "Ukraine"),
    (49.99, 36.23, "Kharkiv", "Ukraine"), (48.46, 35.05, "Dnipro", "Ukraine"),
    (47.01, 28.86, "Chișinău", "Moldova"), (53.68, 23.83, "Hrodna", "Belarus"),
    (52.10, 23.70, "Brest", "Belarus"), (52.44, 31.01, "Homyel", "Belarus"),
    (53.90, 30.33, "Mahilyow", "Belarus"), (55.19, 30.20, "Vitebsk", "Belarus"),
    (54.90, 23.90, "Kaunas", "Lithuania"), (55.70, 21.14, "Klaipėda", "Lithuania"),
    (54.71, 20.51, "Kaliningrad", "Russia"), (58.38, 26.72, "Tartu", "Estonia"),
    (60.71, 28.75, "Vyborg", "Russia"), (61.79, 34.35, "Petrozavodsk", "Russia"),
    (60.45, 22.27, "Turku", "Finland"), (61.50, 23.79, "Tampere", "Finland"),
    (65.01, 25.47, "Oulu", "Finland"), (66.50, 25.73, "Rovaniemi", "Finland"),
    (65.58, 22.15, "Luleå", "Sweden"), (63.83, 20.26, "Umeå", "Sweden"),
    (57.71, 11.97, "Gothenburg", "Sweden"), (55.60, 13.00, "Malmö", "Sweden"),
    (60.39, 5.32, "Bergen", "Norway"), (63.43, 10.39, "Trondheim", "Norway"),
    (45.44, 12.34, "Venice", "Italy"), (45.41, 11.88, "Padua", "Italy"),
    (45.44, 10.99, "Verona", "Italy"), (45.07, 7.69, "Turin", "Italy"),
    (44.49, 11.34, "Bologna", "Italy"), (43.77, 11.26, "Florence", "Italy"),
    (40.85, 14.27, "Naples", "Italy"), (41.39, 2.17, "Barcelona", "Spain"),
    (39.47, -0.38, "Valencia", "Spain"), (37.39, -5.99, "Seville", "Spain"),
    (43.26, -2.93, "Bilbao", "Spain"), (41.15, -8.61, "Porto", "Portugal"),
    (45.76, 4.84, "Lyon", "France"), (43.30, 5.37, "Marseille", "France"),
    (43.60, 1.44, "Toulouse", "France"), (44.84, -0.58, "Bordeaux", "France"),
    (47.22, -1.55, "Nantes", "France"), (48.58, 7.75, "Strasbourg", "France"),
    (43.70, 7.27, "Nice", "France"), (48.78, 9.18, "Stuttgart", "Germany"),
    (50.94, 6.96, "Cologne", "Germany"), (51.34, 12.37, "Leipzig", "Germany"),
    (51.05, 13.74, "Dresden", "Germany"), (49.45, 11.08, "Nuremberg", "Germany"),
    (51.92, 4.48, "Rotterdam", "Netherlands"), (51.22, 4.40, "Antwerp", "Belgium"),
    (53.48, -2.24, "Manchester", "UK"), (52.49, -1.89, "Birmingham", "UK"),
    (55.86, -4.25, "Glasgow", "UK"), (55.95, -3.19, "Edinburgh", "UK"),
    (53.41, -2.99, "Liverpool", "UK"), (48.15, 17.11, "Bratislava", "Slovakia"),
    (46.06, 14.51, "Ljubljana", "Slovenia"), (43.86, 18.41, "Sarajevo", "Bosnia"),
    (41.99, 21.43, "Skopje", "North Macedonia"), (40.64, 22.94, "Thessaloniki", "Greece"),
    (46.77, 23.60, "Cluj-Napoca", "Romania"), (45.76, 21.23, "Timișoara", "Romania"),
    (47.16, 27.59, "Iași", "Romania"), (44.18, 28.65, "Constanța", "Romania"),
    (49.20, 16.61, "Brno", "Czechia"), (50.26, 19.02, "Katowice", "Poland"),
    (53.43, 14.55, "Szczecin", "Poland"), (51.76, 19.46, "Łódź", "Poland"),
    (47.53, 21.63, "Debrecen", "Hungary"), (46.05, 18.23, "Pécs", "Hungary"),
    (35.70, -0.63, "Oran", "Algeria"), (36.75, 3.06, "Algiers", "Algeria"),
    (36.81, 10.18, "Tunis", "Tunisia"), (33.57, -7.59, "Casablanca", "Morocco"),
    (34.02, -6.83, "Rabat", "Morocco"), (35.76, -5.83, "Tangier", "Morocco"),
    (68.97, 33.08, "Murmansk", "Russia"), (54.10, 22.93, "Suwałki", "Poland"),
    (42.51, 27.47, "Burgas", "Bulgaria"), (43.20, 27.91, "Varna", "Bulgaria"),
]

# named physical regions (lat0, lat1, lon0, lon1) for map labels where a city
# name would mislead (e.g. a mountain arc).
LANDMARKS = {
    "the Alps": (44.2, 47.4, 6.0, 14.5), "the Carpathians": (45.0, 49.5, 20.0, 27.0),
    "the Pyrenees": (42.0, 43.6, -1.8, 2.6), "the Apennines": (40.0, 44.4, 10.0, 16.0),
    "the Dinaric Alps": (42.0, 46.2, 15.0, 20.0),
    "the Scandinavian Mts": (60.0, 69.0, 5.0, 14.5),
    "the Suwałki Gap": (53.85, 54.5, 22.0, 23.6),
    "the Kola Peninsula": (67.4, 69.6, 30.0, 41.0),
}


def landmark_at(lat, lon):
    for n, (a0, a1, o0, o1) in LANDMARKS.items():
        if a0 <= lat <= a1 and o0 <= lon <= o1:
            return n
    return None


def map_label(lat, lon):
    """Short label for a bright cluster on a map: a named landmark if the point
    sits in one, else the nearest well-known city (<=90 km), else the region."""
    lm = landmark_at(lat, lon)
    if lm:
        return lm
    name, country, d = nearest_city(lat, lon)
    if d <= 110:
        return name
    reg = region_label(lat, lon)
    return reg or name

# country bounding boxes (lat_min, lat_max, lon_min, lon_max) — only used for the
# rare fallback when a point is >100 km from every listed city.
COUNTRY_BBOX = {
    "Poland": (49.0, 54.9, 14.1, 24.2), "Belarus": (51.2, 56.2, 23.1, 32.8),
    "Ukraine": (44.3, 52.4, 22.1, 40.2), "Finland": (59.8, 70.1, 20.5, 31.6),
    "Sweden": (55.3, 69.1, 11.0, 24.2), "Norway": (57.9, 71.2, 4.5, 31.1),
    "Germany": (47.2, 55.1, 5.8, 15.1), "France": (42.3, 51.1, -4.8, 8.2),
    "Romania": (43.6, 48.3, 20.2, 29.7), "Russia": (50.0, 68.9, 27.3, 40.0),
    "Lithuania": (53.9, 56.5, 20.9, 26.9), "Latvia": (55.6, 58.1, 20.9, 28.2),
    "Estonia": (57.5, 59.7, 21.7, 28.2), "Italy": (36.6, 47.1, 6.6, 18.5),
    "Spain": (36.0, 43.8, -9.3, 3.3), "Czechia": (48.5, 51.1, 12.1, 18.9),
    "Hungary": (45.7, 48.6, 16.1, 22.9), "Bulgaria": (41.2, 44.2, 22.4, 28.6),
}

_R = 6371.0
def _haversine_km(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1); dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * _R * math.asin(min(1.0, math.sqrt(a)))


def nearest_city(lat, lon):
    best, bd = None, 1e9
    for (cla, clo, name, country) in CITIES:
        d = _haversine_km(lat, lon, cla, clo)
        if d < bd:
            bd, best = d, (name, country)
    return best[0], best[1], bd


def region_label(lat, lon):
    """Cardinal region within the containing country, e.g. 'eastern Poland'."""
    cands = [(n, bb) for n, bb in COUNTRY_BBOX.items()
             if bb[0] <= lat <= bb[1] and bb[2] <= lon <= bb[3]]
    if not cands:
        return None
    name, (la0, la1, lo0, lo1) = min(
        cands, key=lambda x: (x[1][1] - x[1][0]) * (x[1][3] - x[1][2]))
    fy = (lat - la0) / (la1 - la0); fx = (lon - lo0) / (lo1 - lo0)
    ns = "north" if fy > 0.62 else "south" if fy < 0.38 else ""
    ew = "east" if fx > 0.62 else "west" if fx < 0.38 else ""
    if ns and ew:
        d = f"{ns}-{ew}ern"
    elif ns:
        d = f"{ns}ern"
    elif ew:
        d = f"{ew}ern"
    else:
        d = "central"
    return f"{d} {name}"


def place_label(lat, lon, max_km=100.0):
    """'near {City}, {Country}' when within max_km of a well-known city, else the
    cardinal region of the containing country, else a lon/lat fallback."""
    name, country, d = nearest_city(lat, lon)
    if d <= max_km:
        return f"near {name}, {country}"
    reg = region_label(lat, lon)
    if reg:
        return reg
    return f"{abs(lat):.1f}°{'N' if lat >= 0 else 'S'}, {abs(lon):.1f}°{'E' if lon >= 0 else 'W'}"


if __name__ == "__main__":
    import json, pathlib
    b = json.load(open(pathlib.Path(__file__).resolve().parents[1] /
                       "website/assets/data/fig3b.json"))
    print("=== pinch-point place labels ===")
    for c in b["circles"]:
        nm, co, d = nearest_city(c["lat"], c["lon"])
        print(f"#{c['rank']:2d} {c['lat']:.2f},{c['lon']:.2f} -> "
              f"{place_label(c['lat'], c['lon']):32s}  (nearest {nm} {d:.0f} km)")
