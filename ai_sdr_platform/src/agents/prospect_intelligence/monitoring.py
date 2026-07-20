from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from ai_sdr_platform.src.agents.prospect_intelligence.models import ProspectIntelligenceResult


@dataclass
class IntelligenceMonitor:
    event_path: str | None = None

    def record(self, result: ProspectIntelligenceResult) -> None:
        if not self.event_path:
            return
        path = Path(self.event_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "account_id": result.account_id,
            "contact_id": result.contact_id,
            "intent_probability": result.intent.probability.value,
            "reply_probability": result.propensity.reply_probability.value,
            "meeting_probability": result.propensity.meeting_probability.value,
            "priority_score": result.ranking.priority_score,
            "signal_count": result.features.signal_count,
            "model_versions": result.model_versions,
        }
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event) + "\n")
