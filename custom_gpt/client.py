"""Stub client for the `custom_gpt` module."""
from __future__ import annotations

from typing import Dict

from custom_gpt.types import HeaderConfig


def build_headers(config: HeaderConfig | None = None) -> Dict[str, str]:
    """Return request headers.

    The real implementation attached role/API-key headers for the port-8000
    backend. The AI SDR backend (port 8011) uses its own JWT auth handled
    elsewhere in app.py, so returning empty headers here is safe — this matches
    the app's existing fallback behavior (see `_api_headers`).
    """
    return {}


__all__ = ["build_headers"]
