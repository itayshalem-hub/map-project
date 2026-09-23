"""Georeferencing: aligning an unreferenced historical photo to real-world coordinates.

find_keypoints() is currently a MOCK. The real implementation will call LightGlue to match
features between the source (historical) image and a target (modern) basemap. The function
signature below is the real contract — swapping in LightGlue later only changes this
function's body, not any caller.

apply_warp() is real: given accepted GCPs, it fits an affine transform from the GCPs (via
rasterio.transform.from_gcps) and writes the source pixels out with that transform as a
GeoTIFF. Deliberately uses rasterio rather than the separate `gdal`/osgeo Python package —
rasterio's PyPI wheels bundle libgdal internally, so this needs no system GDAL install. An
affine fit (rather than a full TPS warp) is a reasonable approximation for near-planar scenes
and keeps this dependency-light; revisit if source imagery has significant lens/terrain
distortion.
"""

from __future__ import annotations

import random
from pathlib import Path

import rasterio
from rasterio.control import GroundControlPoint
from rasterio.transform import from_gcps

from core.data_models import GcpPoint


def find_keypoints(
    source_image_path: str | Path,
    target_image_path: str | Path,
    num_points: int = 8,
    seed: int = 42,
) -> list[GcpPoint]:
    """Return candidate ground-control points matching source pixels to target coordinates.

    MOCK: generates deterministic pseudo-random pairs instead of running LightGlue, so the
    georeferencing review UI can be built and tested without the real model or GPU/torch
    dependencies installed.
    """
    rng = random.Random(seed)
    return [
        GcpPoint(
            source_xy=(rng.uniform(0, 800), rng.uniform(0, 800)),
            target_lonlat=(rng.uniform(34.80, 34.82), rng.uniform(31.90, 31.92)),
            accepted=True,
        )
        for _ in range(num_points)
    ]


def apply_warp(
    source_image_path: str | Path,
    gcps: list[GcpPoint],
    output_path: str | Path,
    dst_srs: str = "EPSG:4326",
) -> Path:
    """Georeference the source image using the accepted GCPs, writing a GeoTIFF.

    Real implementation (not mocked): fits an affine transform from the GCPs and writes the
    original pixels out with that transform, fully testable against synthetic imagery.
    """
    accepted = [g for g in gcps if g.accepted]
    if len(accepted) < 3:
        raise ValueError(f"Need at least 3 accepted GCPs to warp, got {len(accepted)}.")

    rio_gcps = [
        GroundControlPoint(row=py, col=px, x=lon, y=lat)
        for (px, py), (lon, lat) in ((g.source_xy, g.target_lonlat) for g in accepted)
    ]
    transform = from_gcps(rio_gcps)

    with rasterio.open(source_image_path) as src:
        data = src.read()
        profile = src.profile

    profile.update(driver="GTiff", transform=transform, crs=dst_srs)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(data)
    return output_path
