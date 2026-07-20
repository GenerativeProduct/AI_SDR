from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Any


@dataclass
class SDRMetaRankEventStore:
    path: str

    _lock = Lock()

    def append(self, event: dict[str, Any]) -> None:
        target = Path(self.path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with target.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, default=str) + "\n")
