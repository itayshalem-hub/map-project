"""Shared paths, thresholds, and session-state key names used across the app."""

from pathlib import Path

# --- Paths ---
SCRATCH_DIR = Path("./_scratch")  # local working files (gitignored), created at runtime

# --- Pipeline thresholds ---
MIN_GCP_COUNT = 5  # minimum accepted ground-control points before warping
MIN_POLYGON_AREA_M2 = 50.0  # polygons smaller than this are dropped as noise
SIMPLIFY_TOLERANCE_M = 1.0  # Douglas-Peucker simplification tolerance, in meters

# --- Polygon status values ---
STATUS_PENDING = "pending"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"

# --- st.session_state keys ---
SS_STAGE = "stage"  # current pipeline stage: "georeference" | "segment" | "qa" | "export"
SS_SOURCE_IMAGE = "source_image_path"
SS_BASEMAP_IMAGE = "basemap_image_path"
SS_GCPS = "gcps"  # list of GCP dicts pending review
SS_WARPED_RASTER = "warped_raster_path"
SS_POLYGONS = "polygons_gdf"  # the working GeoDataFrame
SS_QUEUE_ORDER = "qa_queue_order"  # fixed list of polygon_ids, sorted by confidence ascending
SS_QUEUE_INDEX = "qa_queue_index"
