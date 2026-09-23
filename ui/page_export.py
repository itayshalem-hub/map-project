"""Stage 4: filter to approved polygons and offer a GeoJSON download."""

from __future__ import annotations

import streamlit as st

import config


def render() -> None:
    st.header("Step 4: Export")

    gdf = st.session_state[config.SS_POLYGONS]
    approved = gdf[gdf["status"] == config.STATUS_APPROVED]

    st.write(f"{len(approved)} approved polygon(s) ready to export.")
    st.dataframe(approved.drop(columns="geometry"))

    if approved.empty:
        st.info("No approved polygons yet — go back to the review queue.")
        return

    geojson_bytes = approved.to_json().encode("utf-8")
    st.download_button(
        "Download GeoJSON",
        data=geojson_bytes,
        file_name="approved_field_polygons.geojson",
        mime="application/geo+json",
        type="primary",
    )
