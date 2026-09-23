"""Generates a fake grayscale "historical photo" and a matching "modern basemap".

Used only for exercising the pipeline end-to-end when no real historical imagery is
available yet. Produces a plain (non-georeferenced) source image resembling a scanned old
aerial photo, and a small georeferenced GeoTIFF basemap for the georeferencing step to
target.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
from PIL import Image, ImageDraw
from rasterio.transform import from_bounds

IMAGE_SIZE = (800, 800)
BASEMAP_BOUNDS = (34.80, 31.90, 34.82, 31.92)  # lon_min, lat_min, lon_max, lat_max


def generate_historical_photo(output_path: str | Path, seed: int = 1) -> Path:
    """Create a grayscale image with a few rectangular field-like shapes, saved as JPEG."""
    rng = np.random.default_rng(seed)
    img = Image.new("L", IMAGE_SIZE, color=200)
    draw = ImageDraw.Draw(img)

    for _ in range(6):
        x0, y0 = rng.integers(0, 600, size=2)
        w, h = rng.integers(80, 200, size=2)
        shade = int(rng.integers(60, 180))
        draw.rectangle([x0, y0, x0 + w, y0 + h], outline=30, fill=shade, width=2)

    # Add grain to look scan-like.
    noise = rng.normal(0, 12, size=(IMAGE_SIZE[1], IMAGE_SIZE[0]))
    arr = np.clip(np.array(img).astype(float) + noise, 0, 255).astype(np.uint8)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(arr, mode="L").save(output_path)
    return output_path


def generate_basemap(output_path: str | Path) -> Path:
    """Create a small georeferenced RGB GeoTIFF standing in for a modern orthophoto."""
    width, height = IMAGE_SIZE
    rng = np.random.default_rng(2)
    base = rng.integers(90, 160, size=(height, width), dtype=np.uint8)
    rgb = np.stack([base, base, base], axis=0)

    transform = from_bounds(*BASEMAP_BOUNDS, width, height)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        output_path,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=3,
        dtype=rgb.dtype,
        crs="EPSG:4326",
        transform=transform,
    ) as dst:
        dst.write(rgb)
    return output_path
