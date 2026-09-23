"""GeoDataFrame schema for the working set of candidate/approved polygons."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

import geopandas as gpd
import pandas as pd
from shapely.geometry.base import BaseGeometry

from config import STATUS_PENDING

POLYGON_SCHEMA_COLUMNS = ["polygon_id", "geometry", "confidence_score", "status"]


@dataclass(frozen=True)
class GcpPoint:
    """A single ground-control point pairing a source-image pixel to a target coordinate."""

    id: str = field(default_factory=lambda: str(uuid4()))
    source_xy: tuple[float, float] = (0.0, 0.0)
    target_lonlat: tuple[float, float] = (0.0, 0.0)
    accepted: bool = True


def empty_polygon_gdf(crs: str = "EPSG:4326") -> gpd.GeoDataFrame:
    """Return an empty GeoDataFrame matching the polygon working schema."""
    return gpd.GeoDataFrame(
        {
            "polygon_id": pd.Series(dtype="str"),
            "geometry": gpd.GeoSeries(dtype="geometry"),
            "confidence_score": pd.Series(dtype="float"),
            "status": pd.Series(dtype="str"),
        },
        crs=crs,
    )


def new_polygon_row(geometry: BaseGeometry, confidence_score: float) -> dict:
    """Build a single polygon record with a fresh id and pending status."""
    return {
        "polygon_id": str(uuid4()),
        "geometry": geometry,
        "confidence_score": confidence_score,
        "status": STATUS_PENDING,
    }


def polygons_to_gdf(rows: list[dict], crs: str = "EPSG:4326") -> gpd.GeoDataFrame:
    """Assemble polygon rows (as produced by new_polygon_row) into a working GeoDataFrame."""
    if not rows:
        return empty_polygon_gdf(crs=crs)
    return gpd.GeoDataFrame(rows, columns=POLYGON_SCHEMA_COLUMNS, crs=crs)
