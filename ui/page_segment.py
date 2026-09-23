"""Stage 2: run segmentation on the georeferenced raster and clean up the results."""

from __future__ import annotations

import streamlit as st

import config
from core.postprocess import clean_polygons
from core.segmentation import segment


def render() -> None:
    st.header("Step 2: Detect field boundaries")
    st.caption(
        "The model scans the aligned photo and proposes field outlines. "
        "You'll review each one in the next step."
    )

    if config.SS_POLYGONS not in st.session_state:
        if st.button("Run detection", type="primary"):
            raw = segment(st.session_state[config.SS_WARPED_RASTER])
            cleaned = clean_polygons(raw)
            st.session_state[config.SS_POLYGONS] = cleaned
            st.session_state[config.SS_QUEUE_INDEX] = 0
            st.rerun()
        return

    gdf = st.session_state[config.SS_POLYGONS]
    st.write(f"Detected {len(gdf)} candidate polygons after cleanup.")
    st.dataframe(gdf.drop(columns="geometry"))

    if st.button("Continue to review queue", type="primary"):
        st.session_state[config.SS_STAGE] = "qa"
        st.rerun()
