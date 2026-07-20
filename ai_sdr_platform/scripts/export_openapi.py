#!/usr/bin/env python3
"""Export OpenAPI schema from the AI SDR FastAPI app."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ai_sdr_platform.src.api.app import create_app

OUTPUT = Path(__file__).resolve().parents[2] / "ai-sdr-frontend" / "openapi" / "openapi.json"


def main() -> None:
    app = create_app()
    schema = app.openapi()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(schema, indent=2), encoding="utf-8")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
