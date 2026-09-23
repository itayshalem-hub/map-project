"""Interactive boundary correction: recompute a single polygon from a user click.

MOCK. The real implementation will run SAM 2 locally in zero-shot mode, prompting it with
the click coordinate to get a refined mask for the field under the cursor. The mock instead
returns a small polygon centered on the click, so the QA queue's "click to refine" wiring can
be built and tested before SAM 2 is integrated.
"""

from __future__ import annotations

from shapely.geometry import Polygon


def refine(
    raster_path: str,
    click_lonlat: tuple[float, float],
    half_size: float = 0.001,
) -> Polygon:
    """Return a replacement polygon for the field boundary nearest the clicked point.

    MOCK: produces a fixed-size square centered on the click instead of running SAM 2.
    """
    lon, lat = click_lonlat
    return Polygon(
        [
            (lon - half_size, lat - half_size),
            (lon + half_size, lat - half_size),
            (lon + half_size, lat + half_size),
            (lon - half_size, lat + half_size),
        ]
    )
