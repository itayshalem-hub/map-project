"""Thin wrapper around streamlit-shortcuts for the QA queue's keyboard-driven workflow.

Native Streamlit has no key-binding primitive. streamlit-shortcuts works by binding a key
combo to an *existing widget's* `key=`, effectively "pressing" that widget (e.g. a button)
when the shortcut fires. So the QA queue page must create real st.button() widgets with the
keys below, and this function just wires the shortcuts to them.

streamlit-shortcuts (confirmed against v1.2.1, and unchanged on its GitHub main as of this
writing) matches shortcut strings directly against the browser's raw
KeyboardEvent.key.toLowerCase() with no aliasing. Its own README documents "space" as a
valid shortcut name, but the real KeyboardEvent.key value for the spacebar is a literal
single-space character (" "), not the word "space" — so the documented usage silently never
fires. Worked around below by binding the literal " " instead.
"""

from __future__ import annotations

from streamlit_shortcuts import add_shortcuts

QA_APPROVE_KEY = "qa_approve_btn"
QA_REJECT_KEY = "qa_reject_btn"
QA_NEXT_KEY = "qa_next_btn"
QA_PREV_KEY = "qa_prev_btn"


def bind_qa_queue_shortcuts() -> None:
    """Bind Space/Backspace/Delete/arrow keys to the QA queue's button widgets.

    Must be called on every rerun after the corresponding st.button(..., key=...) widgets
    have been created, so the shortcut library can find them by key.
    """
    add_shortcuts(
        **{
            QA_APPROVE_KEY: " ",
            QA_REJECT_KEY: ["backspace", "delete"],
            QA_NEXT_KEY: "arrowright",
            QA_PREV_KEY: "arrowleft",
        }
    )
