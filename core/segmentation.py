"""Batch segmentation: detecting candidate field polygons across a georeferenced raster.

MOCK. The real implementation will run a YOLOv11-seg or SegFormer model (fine-tuned on the
partner company's labeled dataset), convert the predicted pixel mask to polygons via
rasterio.features.shapes, and return them in the same schema produced here. Callers only
depend on segment()'s return type (a GeoDataFrame matching POLYGON_SCHEMA_COLUMNS), so the
mock can be replaced without touching the UI or postprocessing code.
"""

from __future__ import annotations

import random
from pathlib import Path

import geopandas as gpd
import rasterio
from shapely.geometry import Polygon

from core.data_models import new_polygon_row, polygons_to_gdf


def segment(
    raster_path: str | Path,
    num_polygons: int = 12,
    seed: int = 7,
) -> gpd.GeoDataFrame:
    """Return candidate field polygons detected across the given georeferenced raster.

    MOCK: scatters synthetic rectangular polygons within the raster's bounds with random
    confidence scores, standing in for real model inference.
    """
    with rasterio.open(raster_path) as src:
        bounds = src.bounds
        crs = src.crs

    rng = random.Random(seed)
    width = bounds.right - bounds.left
    height = bounds.top - bounds.bottom

    rows = []
    for _ in range(num_polygons):
        cell_w = width / 4
        cell_h = height / 4
        origin_x = bounds.left + rng.uniform(0, width - cell_w)
        origin_y = bounds.bottom + rng.uniform(0, height - cell_h)
        w = rng.uniform(cell_w * 0.4, cell_w * 0.9)
        h = rng.uniform(cell_h * 0.4, cell_h * 0.9)

        polygon = Polygon(
            [
                (origin_x, origin_y),
                (origin_x + w, origin_y),
                (origin_x + w, origin_y + h),
                (origin_x, origin_y + h),
            ]
        )
        rows.append(new_polygon_row(polygon, confidence_score=rng.uniform(0.3, 0.98)))

    return polygons_to_gdf(rows, crs=str(crs) if crs else "EPSG:4326")
