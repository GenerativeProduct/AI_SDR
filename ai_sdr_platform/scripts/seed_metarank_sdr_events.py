from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
METARANK_DIR = ROOT / "metarank" / "sdr"
SEED_PATH = METARANK_DIR / "seed-events.jsonl"
EVENTS_PATH = METARANK_DIR / "events.jsonl"


BASE_TIME = datetime(2026, 1, 1, tzinfo=timezone.utc)
SEED_PREFIXES = ("seed-lead-", "seed-ranking-", "seed-interaction-")


LEADS: list[dict[str, Any]] = [
    {
        "id": "seed-lead-high-01",
        "intent_probability": 0.91,
        "reply_probability": 0.76,
        "meeting_probability": 0.64,
        "qualification_probability": 0.81,
    },
    {
        "id": "seed-lead-high-02",
        "intent_probability": 0.86,
        "reply_probability": 0.71,
        "meeting_probability": 0.58,
        "qualification_probability": 0.74,
    },
    {
        "id": "seed-lead-high-03",
        "intent_probability": 0.82,
        "reply_probability": 0.68,
        "meeting_probability": 0.53,
        "qualification_probability": 0.72,
    },
    {
        "id": "seed-lead-mid-01",
        "intent_probability": 0.66,
        "reply_probability": 0.54,
        "meeting_probability": 0.39,
        "qualification_probability": 0.61,
    },
    {
        "id": "seed-lead-mid-02",
        "intent_probability": 0.59,
        "reply_probability": 0.48,
        "meeting_probability": 0.33,
        "qualification_probability": 0.55,
    },
    {
        "id": "seed-lead-mid-03",
        "intent_probability": 0.52,
        "reply_probability": 0.44,
        "meeting_probability": 0.29,
        "qualification_probability": 0.49,
    },
    {
        "id": "seed-lead-low-01",
        "intent_probability": 0.31,
        "reply_probability": 0.24,
        "meeting_probability": 0.16,
        "qualification_probability": 0.27,
    },
    {
        "id": "seed-lead-low-02",
        "intent_probability": 0.24,
        "reply_probability": 0.21,
        "meeting_probability": 0.12,
        "qualification_probability": 0.22,
    },
]


RANKINGS: list[tuple[list[str], tuple[str, str]]] = [
    (
        ["seed-lead-high-01", "seed-lead-mid-01", "seed-lead-low-01", "seed-lead-mid-02"],
        ("seed-lead-high-01", "meeting_booked"),
    ),
    (
        ["seed-lead-high-02", "seed-lead-mid-02", "seed-lead-low-02", "seed-lead-mid-03"],
        ("seed-lead-high-02", "qualified"),
    ),
    (
        ["seed-lead-mid-01", "seed-lead-high-03", "seed-lead-low-01", "seed-lead-low-02"],
        ("seed-lead-high-03", "replied"),
    ),
    (
        ["seed-lead-low-01", "seed-lead-mid-03", "seed-lead-high-01", "seed-lead-low-02"],
        ("seed-lead-high-01", "pricing_request"),
    ),
    (
        ["seed-lead-mid-02", "seed-lead-low-02", "seed-lead-high-02", "seed-lead-mid-01"],
        ("seed-lead-high-02", "meeting_request"),
    ),
    (
        ["seed-lead-low-02", "seed-lead-low-01", "seed-lead-mid-03", "seed-lead-high-03"],
        ("seed-lead-high-03", "interested"),
    ),
    (
        ["seed-lead-mid-01", "seed-lead-mid-02", "seed-lead-low-01", "seed-lead-high-01"],
        ("seed-lead-mid-01", "clicked"),
    ),
    (
        ["seed-lead-low-01", "seed-lead-mid-03", "seed-lead-low-02", "seed-lead-mid-02"],
        ("seed-lead-low-01", "bounced"),
    ),
    (
        ["seed-lead-low-02", "seed-lead-mid-02", "seed-lead-mid-03", "seed-lead-high-02"],
        ("seed-lead-low-02", "unsubscribe"),
    ),
    (
        ["seed-lead-high-01", "seed-lead-high-02", "seed-lead-high-03", "seed-lead-mid-01"],
        ("seed-lead-high-02", "meeting_booked"),
    ),
    (
        ["seed-lead-mid-03", "seed-lead-high-03", "seed-lead-mid-01", "seed-lead-low-01"],
        ("seed-lead-high-03", "qualified"),
    ),
    (
        ["seed-lead-mid-02", "seed-lead-high-01", "seed-lead-low-02", "seed-lead-mid-03"],
        ("seed-lead-high-01", "replied"),
    ),
]


def iso(timestamp: datetime) -> str:
    return timestamp.isoformat().replace("+00:00", "Z")


def item_event(lead: dict[str, Any], timestamp: datetime) -> dict[str, Any]:
    lead_id = lead["id"]
    return {
        "event": "item",
        "id": f"seed-item-{lead_id}",
        "item": lead_id,
        "timestamp": iso(timestamp),
        "fields": [
            {"name": "intent_probability", "value": lead["intent_probability"]},
            {"name": "reply_probability", "value": lead["reply_probability"]},
            {"name": "meeting_probability", "value": lead["meeting_probability"]},
            {"name": "qualification_probability", "value": lead["qualification_probability"]},
        ],
    }


def build_seed_events() -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = [
        item_event(lead, BASE_TIME + timedelta(minutes=index))
        for index, lead in enumerate(LEADS)
    ]
    for index, (items, outcome) in enumerate(RANKINGS, start=1):
        ranking_id = f"seed-ranking-{index:02d}"
        ranking_time = BASE_TIME + timedelta(hours=index)
        events.append(
            {
                "event": "ranking",
                "id": ranking_id,
                "user": f"seed-campaign-{index % 3}",
                "session": ranking_id,
                "timestamp": iso(ranking_time),
                "items": [
                    {"id": item_id, "relevance": 0}
                    for item_id in items
                ],
            }
        )
        outcome_item, outcome_type = outcome
        events.append(
            {
                "event": "interaction",
                "id": f"seed-interaction-{index:02d}",
                "ranking": ranking_id,
                "user": f"seed-campaign-{index % 3}",
                "item": outcome_item,
                "type": outcome_type,
                "position": items.index(outcome_item),
                "timestamp": iso(ranking_time + timedelta(minutes=35)),
            }
        )
    return events


def is_generated_seed(event: dict[str, Any]) -> bool:
    event_id = str(event.get("id", ""))
    item_id = str(event.get("item", ""))
    ranking_id = str(event.get("ranking", ""))
    return (
        event_id.startswith(SEED_PREFIXES)
        or item_id.startswith("seed-lead-")
        or ranking_id.startswith("seed-ranking-")
    )


def read_existing_live_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    live: list[dict[str, Any]] = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        if not is_generated_seed(event):
            live.append(event)
    return live


def sort_key(event: dict[str, Any]) -> tuple[str, str]:
    return (str(event.get("timestamp", "")), str(event.get("id", "")))


def write_jsonl(path: Path, events: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(event, separators=(",", ":")) + "\n" for event in events)
    )


def main() -> None:
    METARANK_DIR.mkdir(parents=True, exist_ok=True)
    seed_events = build_seed_events()
    live_events = read_existing_live_events(EVENTS_PATH)
    write_jsonl(SEED_PATH, seed_events)
    write_jsonl(EVENTS_PATH, sorted(seed_events + live_events, key=sort_key))
    print(f"Wrote {len(seed_events)} seed events to {SEED_PATH}")
    print(f"Wrote {len(seed_events) + len(live_events)} total events to {EVENTS_PATH}")


if __name__ == "__main__":
    main()
