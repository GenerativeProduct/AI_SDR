from __future__ import annotations

from typing import Any

from ai_sdr_platform.src.agents.enrichment.models import (
    EnrichmentAccount,
    EnrichmentCitation,
    EnrichmentContact,
)


def _clean_term(value: str | None) -> str:
    """Drop placeholder values like 'Unknown' so they never pollute a query."""
    v = (value or "").strip()
    if v.lower() in {"unknown", "unknown industry", "unknown location", "n/a", "none"}:
        return ""
    return v


def build_research_queries(account: EnrichmentAccount, contacts: list[EnrichmentContact]) -> list[str]:
    company = account.company_name.strip()
    industry = _clean_term(account.industry)
    location = _clean_term(account.location)
    base = [
        f'"{company}" official website products services',
        f'"{company}" recent news growth expansion',
        f'"{company}" careers hiring {industry}'.strip(),
        f'"{company}" customer reviews competitors',
        f'"{company}" leadership team {location}'.strip(),
    ]
    for contact in contacts[:3]:
        title = _clean_term(contact.title)
        base.append(f'"{contact.full_name}" "{company}" {title} LinkedIn'.strip())
    return list(dict.fromkeys(q.strip() for q in base if q.strip()))


def citations_from_hits(hits: list[dict[str, Any]], limit: int = 8) -> list[EnrichmentCitation]:
    citations: list[EnrichmentCitation] = []
    for hit in hits[:limit]:
        citations.append(
            EnrichmentCitation(
                title=str(hit.get("title") or hit.get("name") or ""),
                url=str(hit.get("url") or hit.get("source_url") or ""),
                snippet=str(hit.get("snippet") or hit.get("text") or hit.get("content") or "")[:700],
                score=_safe_float(hit.get("score")),
            )
        )
    return citations


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def compact_evidence(hits: list[dict[str, Any]], limit: int = 8) -> str:
    lines: list[str] = []
    for idx, hit in enumerate(hits[:limit], start=1):
        title = str(hit.get("title") or hit.get("name") or "Untitled")
        url = str(hit.get("url") or hit.get("source_url") or "")
        snippet = str(hit.get("snippet") or hit.get("text") or hit.get("content") or "")[:900]
        lines.append(f"[{idx}] {title}\nURL: {url}\nSnippet: {snippet}")
    return "\n\n".join(lines)
