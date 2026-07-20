"""Stub types for the `custom_gpt` module."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class HeaderConfig:
    """Placeholder header config.

    Accepts the fields used by app.py and tolerates extras so any additional
    keyword arguments from other call sites do not break.
    """

    apply_role_headers: bool = False
    include_api_key: bool = False
    api_key: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)


__all__ = ["HeaderConfig"]
