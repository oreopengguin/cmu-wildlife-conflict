"""
Raster IO: define the common analysis grid (WGS84, European domain, 10 arc-min)
and read every layer onto it.

  * WorldClim present  : 19 GeoTIFFs inside wc2.1_10m_bio.zip (WGS84)
  * WorldClim future   : single 19-band GeoTIFF (WGS84)
  * gHM                : global 1km GeoTIFF in World Mollweide -> reprojected

All readers return numpy arrays aligned to GRID (same shape, same transform),
with NaN for nodata / out-of-range.
"""
from __future__ import annotations
import zipfile, io
import numpy as np
import rasterio
from rasterio.transform import from_origin
from rasterio.warp import reproject, Resampling
from rasterio.crs import CRS
import config as C


# ----------------------------------------------------------------------------
# The common target grid
# ----------------------------------------------------------------------------
def make_grid():
    """Return (transform, width, height, lons, lats) for the analysis grid."""
    res = C.GRID_RES
    width = int(round((C.LON_MAX - C.LON_MIN) / res))
    height = int(round((C.LAT_MAX - C.LAT_MIN) / res))
    transform = from_origin(C.LON_MIN, C.LAT_MAX, res, res)  # north-up
    lons = C.LON_MIN + (np.arange(width) + 0.5) * res
    lats = C.LAT_MAX - (np.arange(height) + 0.5) * res
    return transform, width, height, lons, lats


GRID_TRANSFORM, GW, GH, GLONS, GLATS = make_grid()
GRID_CRS = CRS.from_epsg(4326)
GRID_SHAPE = (GH, GW)


def _reproject_to_grid(src_arr, src_transform, src_crs, src_nodata=None,
                       resampling=Resampling.bilinear):
    dst = np.full(GRID_SHAPE, np.nan, dtype="float32")
    reproject(
        source=src_arr,
        destination=dst,
        src_transform=src_transform,
        src_crs=src_crs,
        dst_transform=GRID_TRANSFORM,
        dst_crs=GRID_CRS,
        src_nodata=src_nodata,
        dst_nodata=np.nan,
        resampling=resampling,
    )
    return dst


# ----------------------------------------------------------------------------
# WorldClim present (zip of 19 single-band GeoTIFFs)
# ----------------------------------------------------------------------------
def read_worldclim_present(bio_indices):
    zpath = C.DATA_RAW / "wc2.1_10m_bio.zip"
    out = {}
    with zipfile.ZipFile(zpath) as z:
        names = {n.lower(): n for n in z.namelist() if n.lower().endswith(".tif")}
        for b in bio_indices:
            key = f"wc2.1_10m_bio_{b}.tif"
            match = names.get(key.lower())
            if match is None:
                match = next(n for k, n in names.items() if k.endswith(f"bio_{b}.tif"))
            with z.open(match) as fh:
                data = fh.read()
            with rasterio.open(io.BytesIO(data)) as ds:
                arr = ds.read(1).astype("float32")
                nod = ds.nodata
                if nod is not None:
                    arr[arr == nod] = np.nan
                arr[arr < -3.0e38] = np.nan
                out[b] = _reproject_to_grid(arr, ds.transform, ds.crs, src_nodata=nod)
    return out


# ----------------------------------------------------------------------------
# WorldClim future (single multi-band GeoTIFF; band k = BIO k)
# ----------------------------------------------------------------------------
def read_worldclim_future(bio_indices, scenario=None):
    scen = scenario or C.SCENARIO
    fpath = C.DATA_RAW / f"wc2.1_10m_bioc_MPI-ESM1-2-HR_{scen}_2081-2100.tif"
    out = {}
    with rasterio.open(fpath) as ds:
        for b in bio_indices:
            arr = ds.read(b).astype("float32")
            nod = ds.nodata
            if nod is not None:
                arr[arr == nod] = np.nan
            arr[arr < -3.0e38] = np.nan
            out[b] = _reproject_to_grid(arr, ds.transform, ds.crs, src_nodata=nod)
    return out


# ----------------------------------------------------------------------------
# Global Human Modification (Mollweide 1km) -> reprojected & resampled
# ----------------------------------------------------------------------------
def read_ghm():
    import glob
    cands = glob.glob(str(C.DATA_RAW / "gHM_extracted" / "*.tif"))
    if not cands:
        cands = glob.glob(str(C.DATA_RAW / "**" / "gHM*.tif"), recursive=True)
    fpath = cands[0]
    with rasterio.open(fpath) as ds:
        # windowed reproject: reproject handles the full array; gHM ~ 43k x 21k
        # is large, so read at a decimated overview to stay in memory, then warp.
        scale = 8  # read at ~8km native, still finer than our 18km grid
        out_h = ds.height // scale
        out_w = ds.width // scale
        arr = ds.read(
            1, out_shape=(out_h, out_w), resampling=Resampling.average
        ).astype("float32")
        nod = ds.nodata
        if nod is not None:
            arr[arr == nod] = np.nan
        # gHM stored 0..1 (float) or 0..65536 scaled int in some versions
        finite = np.isfinite(arr)
        if finite.any() and np.nanmax(arr[finite]) > 1.5:
            arr = arr / 65536.0
        arr[arr < 0] = np.nan
        # build the decimated transform
        dec_transform = ds.transform * ds.transform.scale(
            ds.width / out_w, ds.height / out_h
        )
        H = _reproject_to_grid(arr, dec_transform, ds.crs, src_nodata=np.nan,
                               resampling=Resampling.average)
    return H


def land_mask(present_stack):
    """Cells with valid climate = land within domain."""
    ref = next(iter(present_stack.values()))
    return np.isfinite(ref)


if __name__ == "__main__":
    print("grid:", GRID_SHAPE, "lon", GLONS[0], GLONS[-1], "lat", GLATS[0], GLATS[-1])
