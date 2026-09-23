"""Stage 3: keyboard-driven QA queue — the core review interaction.

The queue order is fixed once, at entry to this stage, as all polygon_ids sorted by
confidence ascending (lowest-confidence, most-likely-wrong polygons reviewed first). Arrow
keys move through this fixed order without changing status; Space/Backspace set the current
polygon's status and auto-advance. "Redraw boundary" re-runs the (mocked) SAM 2 boundary
refinement for the current polygon, prompted at its centroid.

The map is a static HTML embed (folium's own _repr_html_, via st.components.v1.html) rather
than the interactive streamlit-folium component, and refinement is button-triggered rather
than click-triggered on the map. This trades away literal click-to-refine for reliability:
streamlit-folium's iframe was found to permanently stick at height=0 whenever first mounted
via a programmatic st.rerun() — which is how every page in this app is reached — so it never
rendered at all.
"""

from __future__ import annotations

import folium
import streamlit as st
import streamlit.components.v1 as components

import config
from core.sam_refine import refine
from utils.keyboard import (
    QA_APPROVE_KEY,
    QA_NEXT_KEY,
    QA_PREV_KEY,
    QA_REJECT_KEY,
    bind_qa_queue_shortcuts,
)

QA_MAP_HEIGHT = 450


def _init_queue_order() -> None:
    if config.SS_QUEUE_ORDER in st.session_state:
        return
    gdf = st.session_state[config.SS_POLYGONS]
    pending = gdf[gdf["status"] == config.STATUS_PENDING]
    ordered_ids = pending.sort_values("confidence_score")["polygon_id"].tolist()
    st.session_state[config.SS_QUEUE_ORDER] = ordered_ids
    st.session_state[config.SS_QUEUE_INDEX] = 0


def _current_polygon_id() -> str | None:
    order = st.session_state[config.SS_QUEUE_ORDER]
    index = st.session_state[config.SS_QUEUE_INDEX]
    if not order or index >= len(order):
        return None
    return order[index]


def _set_status(polygon_id: str, status: str) -> None:
    gdf = st.session_state[config.SS_POLYGONS]
    gdf.loc[gdf["polygon_id"] == polygon_id, "status"] = status
    st.session_state[config.SS_POLYGONS] = gdf


def _advance() -> None:
    order = st.session_state[config.SS_QUEUE_ORDER]
    st.session_state[config.SS_QUEUE_INDEX] = min(
        st.session_state[config.SS_QUEUE_INDEX] + 1, len(order)
    )


def _go_next() -> None:
    order = st.session_state[config.SS_QUEUE_ORDER]
    st.session_state[config.SS_QUEUE_INDEX] = min(
        st.session_state[config.SS_QUEUE_INDEX] + 1, len(order) - 1
    )


def _go_prev() -> None:
    st.session_state[config.SS_QUEUE_INDEX] = max(
        st.session_state[config.SS_QUEUE_INDEX] - 1, 0
    )


def _handle_approve() -> None:
    polygon_id = _current_polygon_id()
    if polygon_id is not None:
        _set_status(polygon_id, config.STATUS_APPROVED)
        _advance()


def _handle_reject() -> None:
    polygon_id = _current_polygon_id()
    if polygon_id is not None:
        _set_status(polygon_id, config.STATUS_REJECTED)
        _advance()


def render() -> None:
    st.header("Step 3: Review queue")
    st.caption(
        "Space = approve, Backspace/Delete = reject, arrows = navigate without changing "
        "status. Use \"Redraw boundary\" to re-run boundary refinement on the current polygon."
    )
    _init_queue_order()

    order = st.session_state[config.SS_QUEUE_ORDER]
    index = st.session_state[config.SS_QUEUE_INDEX]

    if not order:
        st.info("No pending polygons to review.")
        if st.button("Continue to export", type="primary"):
            st.session_state[config.SS_STAGE] = "export"
            st.rerun()
        return

    if index >= len(order):
        st.success("Queue complete — every polygon has been reviewed.")
        if st.button("Continue to export", type="primary"):
            st.session_state[config.SS_STAGE] = "export"
            st.rerun()
        return

    st.progress((index + 1) / len(order), text=f"Polygon {index + 1} of {len(order)}")

    polygon_id = order[index]
    gdf = st.session_state[config.SS_POLYGONS]
    row = gdf.loc[gdf["polygon_id"] == polygon_id].iloc[0]
    st.write(f"Confidence score: {row['confidence_score']:.2f}")

    geometry = row["geometry"]
    minx, miny, maxx, maxy = geometry.bounds
    center = ((miny + maxy) / 2, (minx + maxx) / 2)

    fmap = folium.Map(location=center, zoom_start=17)
    folium.GeoJson(geometry, style_function=lambda _: {"color": "orange", "weight": 3}).add_to(
        fmap
    )
    fmap.fit_bounds([[miny, minx], [maxy, maxx]])
    # fmap._repr_html_() alone emits a Jupyter-specific "trust this notebook" banner
    # instead of the map; wrapping in a Figure first renders the real standalone HTML.
    figure = folium.Figure().add_child(fmap)
    components.html(figure.render(), height=QA_MAP_HEIGHT)

    if st.button("Redraw boundary (SAM 2 refine)"):
        centroid = geometry.centroid
        new_geometry = refine(
            st.session_state[config.SS_WARPED_RASTER],
            (centroid.x, centroid.y),
        )
        gdf.loc[gdf["polygon_id"] == polygon_id, "geometry"] = new_geometry
        st.session_state[config.SS_POLYGONS] = gdf
        st.rerun()

    cols = st.columns(4)
    with cols[0]:
        if st.button("Approve (Space)", key=QA_APPROVE_KEY, type="primary"):
            _handle_approve()
            st.rerun()
    with cols[1]:
        if st.button("Reject (Backspace)", key=QA_REJECT_KEY):
            _handle_reject()
            st.rerun()
    with cols[2]:
        if st.button("◀ Prev", key=QA_PREV_KEY, disabled=index == 0):
            _go_prev()
            st.rerun()
    with cols[3]:
        if st.button("Next ▶", key=QA_NEXT_KEY, disabled=index >= len(order) - 1):
            _go_next()
            st.rerun()

    bind_qa_queue_shortcuts()
