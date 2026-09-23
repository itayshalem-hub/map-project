# GeoAI Historical Aerial Photo → Field Polygons

**Live demo:** https://map-project-snaetqcsredxvm7dy3ccau.streamlit.app/

Streamlit demo: turns a historical (unreferenced) aerial photo into a GeoJSON of approved
agricultural field polygons via georeferencing → auto-segmentation → keyboard-driven QA
review → export.

**Status:** all AI models (LightGlue keypoint matching, YOLO/SegFormer segmentation, SAM 2
boundary refinement) are currently **mocked** — see the module docstrings in `core/` for
each mock's real-model contract. This lets the full pipeline and UI be exercised end-to-end
with synthetic data before any real model or training data is wired in.

## Setup (macOS / Apple Silicon)

No system GDAL install (e.g. Homebrew) is required — `rasterio` and `geopandas` ship
prebuilt wheels with libgdal bundled in.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

On first load, click **"Generate synthetic test data"** to create a fake historical photo
and basemap, then walk through all four pipeline stages.

## Tests

```bash
pytest
```
