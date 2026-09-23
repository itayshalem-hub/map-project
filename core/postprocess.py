"""Geometry cleanup applied to raw segmentation output: simplification and noise removal.

Unlike the model wrappers in this package, this logic is real (not mocked) — it is cheap,
deterministic, and independently testable regardless of whether the upstream polygons came
from the mock segmenter or a real trained model.

Both operations here are defined in meters (SIMPLIFY_TOLERANCE_M, MIN_POLYGON_AREA_M2), but
the working GeoDataFrame is typically in a geographic CRS (EPSG:4326, degrees). Applying a
metric tolerance/threshold directly to degree coordinates is meaningless (a "1 meter"
tolerance is actually ~111km in degrees) and silently drops or over-simplifies everything.
To avoid every caller having to remember this, both functions reproject internally to an
auto-detected local UTM CRS to do the metric work, then reproject back to the input CRS.
"""

from __future__ import annotations

import geopandas as gpd

from config import MIN_POLYGON_AREA_M2, SIMPLIFY_TOLERANCE_M


def _in_metric_crs(gdf: gpd.GeoDataFrame) -> tuple[gpd.GeoDataFrame, "pyproj.CRS"]:
    """Return (gdf reprojected to a local UTM CRS, the original CRS to reproject back to)."""
    original_crs = gdf.crs
    if original_crs is not None and original_crs.is_geographic:
        utm_crs = gdf.estimate_utm_crs()
        return gdf.to_crs(utm_crs), original_crs
    return gdf, original_crs


def simplify_polygons(
    gdf: gpd.GeoDataFrame, tolerance: float = SIMPLIFY_TOLERANCE_M
) -> gpd.GeoDataFrame:
    """Apply Douglas-Peucker simplification (in meters) to every geometry."""
    if gdf.empty:
        return gdf
    metric_gdf, original_crs = _in_metric_crs(gdf)
    simplified = metric_gdf.copy()
    simplified["geometry"] = simplified.geometry.simplify(tolerance, preserve_topology=True)
    return simplified.to_crs(original_crs) if original_crs is not None else simplified


def drop_small_polygons(
    gdf: gpd.GeoDataFrame, min_area_m2: float = MIN_POLYGON_AREA_M2
) -> gpd.GeoDataFrame:
    """Remove polygons below the minimum area (in square meters), treated as noise."""
    if gdf.empty:
        return gdf
    metric_gdf, _ = _in_metric_crs(gdf)
    keep_mask = metric_gdf.geometry.area >= min_area_m2
    return gdf[keep_mask.to_numpy()].reset_index(drop=True)


def clean_polygons(
    gdf: gpd.GeoDataFrame,
    tolerance: float = SIMPLIFY_TOLERANCE_M,
    min_area_m2: float = MIN_POLYGON_AREA_M2,
) -> gpd.GeoDataFrame:
    """Run the full cleanup pass: simplify first, then drop what's left that's too small."""
    return drop_small_polygons(simplify_polygons(gdf, tolerance), min_area_m2)
