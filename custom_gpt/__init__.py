"""Lightweight stub for the `custom_gpt` module.

The original `custom_gpt` package was part of the larger monorepo this folder was
extracted from, and is not required for the AI SDR flow. This stub lets
`app.py` import and run. The "Custom GPT" tab shows a placeholder; every other
tab works normally.

To restore full functionality, replace this folder with the real `custom_gpt`
package from the original repo.
"""
from __future__ import annotations


def render_custom_gpt_tab(base_url: str) -> None:
    import streamlit as st

    st.info(
        "The Custom GPT tab is not available in this build — the `custom_gpt` "
        "module was not included when this project was extracted from its "
        "original repo. All AI SDR features on the other tabs work normally."
    )
    st.caption(f"(Configured backend base URL: {base_url})")


__all__ = ["render_custom_gpt_tab"]
