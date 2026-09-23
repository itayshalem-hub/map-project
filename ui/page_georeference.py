"""Stage 1: review AI-suggested ground-control points, then warp the source image.

Split-screen: the raw historical photo (plain image, click to place/nudge a point) next to
the modern basemap. The operator accepts or rejects each suggested GCP pair; once at least
MIN_GCP_COUNT are accepted, "Run Warp" produces a georeferenced GeoTIFF and advances the
pipeline to the segmentation stage.

The basemap is rendered via a static HTML embed (folium's own _repr_html_, through
st.components.v1.html) rather than the streamlit-folium interactive component. This map
only needs to display GCP markers here, not capture clicks, and the static embed sidesteps a
confirmed component-remounting bug in streamlit-folium: its iframe permanently sticks at
height=0 when first mounted via a programmatic st.rerun(), which is exactly how every page
in this app is reached, so the interactive map never rendered at all.
"""

from __future__ import annotations

from pathlib import Path

import folium
import streamlit as st
import streamlit.components.v1 as components
from streamlit_image_coordinates import streamlit_image_coordinates

import config
from core.georeferencing import apply_warp, find_keypoints
from core.data_models import GcpPoint

GEOREF_MAP_HEIGHT = 400

SCRATCH_WARPED_PATH = config.SCRATCH_DIR / "warped.tif"


def _init_gcps() -> None:
    if config.SS_GCPS not in st.session_state:
        st.session_state[config.SS_GCPS] = find_keypoints(
            st.session_state[config.SS_SOURCE_IMAGE],
            st.session_state[config.SS_BASEMAP_IMAGE],
        )


def _render_gcp_row(index: int, gcp: GcpPoint) -> None:
    cols = st.columns([4, 2, 2])
    cols[0].write(
        f"Point {index + 1}: source px {gcp.source_xy} → "
        f"target {gcp.target_lonlat[0]:.5f}, {gcp.target_lonlat[1]:.5f}"
    )
    if cols[1].button("Accept", key=f"gcp_accept_{gcp.id}"):
        _set_gcp_accepted(index, True)
    if cols[2].button("Reject", key=f"gcp_reject_{gcp.id}"):
        _set_gcp_accepted(index, False)


def _set_gcp_accepted(index: int, accepted: bool) -> None:
    gcps: list[GcpPoint] = st.session_state[config.SS_GCPS]
    gcps[index] = GcpPoint(
        id=gcps[index].id,
        source_xy=gcps[index].source_xy,
        target_lonlat=gcps[index].target_lonlat,
        accepted=accepted,
    )
    st.session_state[config.SS_GCPS] = gcps


def render() -> None:
    st.header("Step 1: Georeferencing — align the historical photo")
    st.caption(
        "Review the suggested match points between the old photo and the modern map. "
        "Accept or reject each one, then run the alignment."
    )
    _init_gcps()

    left, right = st.columns(2)
    with left:
        st.subheader("Historical photo")
        click = streamlit_image_coordinates(
            st.session_state[config.SS_SOURCE_IMAGE], key="georef_source_click"
        )
        if click is not None:
            st.caption(f"Last click: x={click['x']}, y={click['y']}")

    with right:
        st.subheader("Modern basemap")
        gcps: list[GcpPoint] = st.session_state[config.SS_GCPS]
        center = (
            gcps[0].target_lonlat[1] if gcps else 31.95,
            gcps[0].target_lonlat[0] if gcps else 34.85,
        )
        fmap = folium.Map(location=center, zoom_start=15)
        for gcp in gcps:
            color = "green" if gcp.accepted else "red"
            folium.CircleMarker(
                location=(gcp.target_lonlat[1], gcp.target_lonlat[0]),
                radius=6,
                color=color,
                fill=True,
            ).add_to(fmap)
        # fmap._repr_html_() alone emits a Jupyter-specific "trust this notebook" banner
        # instead of the map; wrapping in a Figure first renders the real standalone HTML.
        figure = folium.Figure().add_child(fmap)
        components.html(figure.render(), height=GEOREF_MAP_HEIGHT)

    st.divider()
    gcps: list[GcpPoint] = st.session_state[config.SS_GCPS]
    for i, gcp in enumerate(gcps):
        _render_gcp_row(i, gcp)

    accepted_count = sum(1 for g in gcps if g.accepted)
    st.divider()
    st.write(f"Accepted points: {accepted_count} / {config.MIN_GCP_COUNT} required")

    if accepted_count < config.MIN_GCP_COUNT:
        st.button("Run Warp", disabled=True)
        st.info(f"Accept at least {config.MIN_GCP_COUNT} points to continue.")
        return

    if st.button("Run Warp", type="primary"):
        output_path = apply_warp(
            st.session_state[config.SS_SOURCE_IMAGE],
            gcps,
            SCRATCH_WARPED_PATH,
        )
        st.session_state[config.SS_WARPED_RASTER] = str(output_path)
        st.session_state[config.SS_STAGE] = "segment"
        st.rerun()
