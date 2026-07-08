"""
Entropic optimal transport between present and future habitat-suitability
surfaces (Cuturi 2013; Peyre & Cuturi 2019).

Design note: a single-Gaussian convolutional Sinkhorn cannot move mass across
the 100-500 km gaps that real climate range-shifts require (the heat kernel
vanishes at long range and the barycentric map collapses to the domain
centroid). We therefore solve a *proper* entropic OT on a coarsened grid with an
explicit great-circle cost matrix (POT), then upsample the resulting
displacement field back to full resolution. This yields physically correct,
long-range, poleward displacements.

Products:
  * Wasserstein-2 range-shift distance (km)
  * Entropic Displacement Field  D(x) = T(x) - x  (dlon, dlat)
  * Coexistence Friction         F(x) = < D(x), grad H(x) >_+
"""
from __future__ import annotations
import numpy as np
from scipy.ndimage import gaussian_filter, zoom
import ot as pot
import config as C


def haversine_km(lon1, lat1, lon2, lat2):
    R = 6371.0
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlmb = np.radians(lon2 - lon1)
    h = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dlmb / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(h))


def _coarsen(field, mask, lons, lats, cf):
    """Block-average a field and mask by factor cf; return coarse field, coarse
    land mask, and coarse cell-center lon/lat grids."""
    ny, nx = field.shape
    ny2, nx2 = (ny // cf) * cf, (nx // cf) * cf
    fm = np.where(mask, field, np.nan)[:ny2, :nx2]
    m = mask[:ny2, :nx2].astype(float)
    fb = fm.reshape(ny2 // cf, cf, nx2 // cf, cf)
    mb = m.reshape(ny2 // cf, cf, nx2 // cf, cf)
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        cf_field = np.nanmean(fb, axis=(1, 3))
    land_frac = mb.mean(axis=(1, 3))
    cmask = land_frac >= 0.5
    clon = lons[:nx2].reshape(nx2 // cf, cf).mean(1)
    clat = lats[:ny2].reshape(ny2 // cf, cf).mean(1)
    CLON, CLAT = np.meshgrid(clon, clat)
    cf_field = np.where(cmask & np.isfinite(cf_field), cf_field, 0.0)
    return cf_field, cmask, CLON, CLAT


def analyze_pair(present, future, H, mask, lons, lats, cf=5, reg_frac=0.02,
                 n_iter=3000):
    """Full OT analysis for one suitability pair via coarse-grid entropic OT."""
    cP, cmask, CLON, CLAT = _coarsen(present, mask, lons, lats, cf)
    cF, _, _, _ = _coarsen(future, mask, lons, lats, cf)

    land = cmask.ravel()
    lon_c = CLON.ravel()[land]
    lat_c = CLAT.ravel()[land]
    a = np.clip(cP.ravel()[land], 0, None)
    b = np.clip(cF.ravel()[land], 0, None)
    if a.sum() == 0 or b.sum() == 0:
        raise ValueError("empty measure")
    a = a / a.sum()
    b = b / b.sum()

    # great-circle squared-distance cost (km^2), scaled for conditioning
    LO1, LO2 = np.meshgrid(lon_c, lon_c)
    LA1, LA2 = np.meshgrid(lat_c, lat_c)
    Dkm = haversine_km(LO1, LA1, LO2, LA2)
    Ckm2 = Dkm ** 2
    Cn = Ckm2 / Ckm2.mean()
    reg = reg_frac                      # entropic reg on normalized cost

    P = pot.sinkhorn(a, b, Cn, reg, numItermax=n_iter, stopThr=1e-9)

    # barycentric map T_i = sum_j P_ij center_j / a_i
    ai = a + 1e-12
    T_lon = (P @ lon_c) / ai
    T_lat = (P @ lat_c) / ai
    d_lon_c = T_lon - lon_c
    d_lat_c = T_lat - lat_c

    W_km = float(np.sqrt(np.sum(P * Ckm2)))

    # scatter coarse displacement back onto the coarse 2D grid, then upsample
    ny_c, nx_c = cmask.shape
    DLON_c = np.zeros((ny_c, nx_c)); DLAT_c = np.zeros((ny_c, nx_c))
    idx = np.flatnonzero(cmask.ravel())
    DLON_c.ravel()[idx] = d_lon_c
    DLAT_c.ravel()[idx] = d_lat_c
    # smooth on coarse grid then upsample to full grid
    DLON_c = gaussian_filter(DLON_c, 0.8)
    DLAT_c = gaussian_filter(DLAT_c, 0.8)
    ny, nx = mask.shape
    dlon = zoom(DLON_c, (ny / ny_c, nx / nx_c), order=1)[:ny, :nx]
    dlat = zoom(DLAT_c, (ny / ny_c, nx / nx_c), order=1)[:ny, :nx]
    dlon = np.where(mask, dlon, 0.0)
    dlat = np.where(mask, dlat, 0.0)

    F = coexistence_friction(dlon, dlat, H, mask, lons, lats)
    LON, LAT = np.meshgrid(lons, lats)
    shift = haversine_km(LON, LAT, LON + dlon, LAT + dlat)
    a_full = np.where(mask, np.clip(present, 0, None), 0.0)
    a_full = a_full / (a_full.sum() + 1e-12)
    return dict(dlon=dlon, dlat=dlat, W_km=W_km, friction=F,
                shift_km=np.where(mask, shift, np.nan), a=a_full)


def coexistence_friction(dlon, dlat, H, mask, lons, lats, smooth=1.0):
    """F(x) = positive part of <displacement, grad H>. Displacement pushing a
    species UP the human-pressure gradient => mechanistic conflict pressure.
    Gradients in km-normalized geographic space (isotropic)."""
    Hs = gaussian_filter(np.where(np.isfinite(H), H, 0.0), smooth)
    dlat_deg = float(np.abs(lats[1] - lats[0]))
    dlon_deg = float(np.abs(lons[1] - lons[0]))
    LAT = np.meshgrid(lons, lats)[1]
    km_per_deg_lat = 111.0
    km_per_deg_lon = 111.0 * np.cos(np.radians(LAT))
    gH_lat, gH_lon = np.gradient(Hs, dlat_deg, dlon_deg)
    gH_lat_km = gH_lat / km_per_deg_lat
    gH_lon_km = gH_lon / km_per_deg_lon
    d_lon_km = dlon * km_per_deg_lon
    d_lat_km = dlat * km_per_deg_lat
    dot = d_lon_km * gH_lon_km + d_lat_km * gH_lat_km
    return np.where(mask, np.clip(dot, 0, None), 0.0)
