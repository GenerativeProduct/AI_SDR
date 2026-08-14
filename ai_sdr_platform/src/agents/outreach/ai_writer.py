"""LLM-powered outreach copy generation.

Reads a prospect's enrichment (company summary, signals, pain points) plus the
contact's name/title/company and asks a local model (Ollama, e.g. llama3.1:8b) to
write a natural, personalized email or LinkedIn message. Falls back to None on any
failure so the caller keeps the deterministic template.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger("sdr.outreach")


_PROMPT = """You are an expert B2B SDR writing a short, highly personalized cold {channel} message.

Recipient: {name}, {title} at {company}.

Use ONLY the research below — do not invent facts, numbers, or events. If a detail
isn't provided, don't reference it.

Company research:
{summary}

Observed signals:
{signals}

Likely pain points:
{pains}

What we offer: {offer}

Rules:
- Keep it concise and human: 3-5 short sentences for email, 2-3 for linkedin.
- Open with something specific to THIS company (from the research), not a generic hook.
- Connect one pain point to our offer as a hypothesis, not a stated fact.
- End with a soft ask for a brief 15-minute conversation.
- No "I hope this finds you well", no buzzword soup, no fake urgency.
- Address the person by first name only.

Return ONLY valid JSON, nothing else:
{{"subject": "<short subject, empty string for linkedin>", "body": "<the message>"}}
"""


def _extract_json(raw: str) -> dict[str, Any]:
    if not raw:
        return {}
    # Grab the first {...} block, tolerant of markdown fences / extra prose.
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return {}
    try:
        return json.loads(match.group(0))
    except Exception:
        return {}


def _bullets(items: list[str] | None, empty: str) -> str:
    items = [str(i).strip() for i in (items or []) if str(i).strip()]
    if not items:
        return empty
    return "\n".join(f"- {i}" for i in items[:6])


def generate_message(
    llm_router: Any,
    *,
    channel: str,
    first_name: str,
    title: str,
    company: str,
    company_summary: str,
    signals: list[str] | None,
    pain_points: list[str] | None,
    offer: str,
    model_name: str,
    provider: str = "ollama_local",
) -> dict[str, str] | None:
    """Return {"subject", "body"} written by the LLM, or None on failure."""
    if llm_router is None:
        return None
    prompt = _PROMPT.format(
        channel=channel,
        name=first_name or "there",
        title=title or "the team",
        company=company or "the company",
        summary=(company_summary or "(no company summary available)").strip()[:1500],
        signals=_bullets(signals, "(no strong signals found)"),
        pains=_bullets(pain_points, "(no confirmed pain points)"),
        offer=offer,
    )
    try:
        raw = llm_router.complete(
            prompt=prompt,
            provider=provider,
            max_tokens=600,
            model_name=model_name,
        )
    except Exception as exc:
        logger.error("AI outreach generation call failed for %s@%s: %s", first_name, company, exc)
        return None

    data = _extract_json(raw)
    body = str(data.get("body") or "").strip()
    if not body:
        logger.warning("AI outreach generation returned no usable body for %s@%s", first_name, company)
        return None
    subject = str(data.get("subject") or "").strip()
    logger.info("AI outreach %s written for %s@%s (%d chars)", channel, first_name, company, len(body))
    return {"subject": subject, "body": body}
