"""Streamlit entrypoint: routes between pipeline stages based on session state.

Stages: upload/generate -> georeference -> segment -> qa -> export. The current stage is
tracked in st.session_state[config.SS_STAGE] and each stage's page module owns advancing to
the next one once its work is done.
"""

from __future__ import annotations

import streamlit as st

import config
from ui import page_export, page_georeference, page_qa_queue, page_segment
from utils.synthetic_data import generate_basemap, generate_historical_photo

st.set_page_config(page_title="GeoAI Field Extraction", layout="wide")

SCRATCH_SOURCE_PATH = config.SCRATCH_DIR / "historical_photo.jpg"
SCRATCH_BASEMAP_PATH = config.SCRATCH_DIR / "basemap.tif"


def _render_intro() -> None:
    st.header("GeoAI Historical Aerial Photo → Field Polygons")
    st.caption(
        "Demo build: every AI step below (matching, detection, boundary refinement) is "
        "currently a mocked stand-in, so the full workflow can be exercised without real "
        "imagery or trained models."
    )
    st.write(
        "No historical imagery is loaded yet. Generate a synthetic test photo and basemap "
        "to walk through the pipeline."
    )
    if st.button("Generate synthetic test data", type="primary"):
        source_path = generate_historical_photo(SCRATCH_SOURCE_PATH)
        basemap_path = generate_basemap(SCRATCH_BASEMAP_PATH)
        st.session_state[config.SS_SOURCE_IMAGE] = str(source_path)
        st.session_state[config.SS_BASEMAP_IMAGE] = str(basemap_path)
        st.session_state[config.SS_STAGE] = "georeference"
        st.rerun()


def main() -> None:
    stage = st.session_state.get(config.SS_STAGE)

    if stage is None or config.SS_SOURCE_IMAGE not in st.session_state:
        _render_intro()
        return

    st.sidebar.write("**Pipeline stage**")
    st.sidebar.write(
        {
            "georeference": "1. Georeferencing",
            "segment": "2. Detection",
            "qa": "3. Review queue",
            "export": "4. Export",
        }.get(stage, stage)
    )

    if stage == "georeference":
        page_georeference.render()
    elif stage == "segment":
        page_segment.render()
    elif stage == "qa":
        page_qa_queue.render()
    elif stage == "export":
        page_export.render()
    else:
        st.error(f"Unknown pipeline stage: {stage!r}")


if __name__ == "__main__":
    main()
