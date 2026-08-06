from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol

import requests

logger = logging.getLogger("sdr.enrichment")

from ai_sdr_platform.src.agents.enrichment.models import (
    EnrichmentAccount,
    EnrichmentResearchRequest,
    EnrichmentResult,
    EnrichmentSignal,
)
from ai_sdr_platform.src.agents.enrichment.prompts import ENRICHMENT_SYNTHESIS_PROMPT
from ai_sdr_platform.src.agents.enrichment.repository import EnrichmentRepository
from ai_sdr_platform.src.agents.enrichment.tools import build_research_queries, citations_from_hits, compact_evidence
from ai_sdr_platform.src.shared.config import settings


class SearchProvider(Protocol):
    def search(
        self,
        *,
        query: str,
        collection: str,
        top_k: int,
        provider: str | None,
        auto_fetch_and_index: bool,
        llm_provider: str,
    ) -> dict[str, Any]:
        ...


@dataclass
class DirectOpenSearchProvider:
    opensearch_web: Any
    tenant_id: str = "default"
    role: str = "viewer"

    def search(
        self,
        *,
        query: str,
        collection: str,
        top_k: int,
        provider: str | None,
        auto_fetch_and_index: bool,
        llm_provider: str,
    ) -> dict[str, Any]:
        result = self.opensearch_web.search(
            query=query,
            collection=collection,
            tenant_id=self.tenant_id,
            role=self.role,
            top_k=top_k,
            provider=provider,
            auto_fetch_and_index=auto_fetch_and_index,
        )
        explanation = self.opensearch_web.explain(
            query,
            result.get("hits", []),
            llm_provider=llm_provider,
        )
        return {**result, "explanation": explanation}


class NoopSearchProvider:
    def search(
        self,
        *,
        query: str,
        collection: str,
        top_k: int,
        provider: str | None,
        auto_fetch_and_index: bool,
        llm_provider: str,
    ) -> dict[str, Any]:
        return {
            "query": query,
            "hits": [],
            "explanation": "",
            "provider": provider or "none",
            "warnings": ["No OpenSearch provider configured for enrichment."],
        }


@dataclass
class SearxngSearchProvider:
    """Live web-search provider backed by a local SearXNG instance.

    Used for enrichment when the optional OpenSearch backend service is not
    available. SearXNG's JSON API returns ``results: [{title, url, content}]``,
    which we map to the hit shape the enrichment synthesis step expects.
    """

    base_url: str
    timeout_seconds: float = 15.0
    name: str = "searxng"

    def search(
        self,
        *,
        query: str,
        collection: str,
        top_k: int,
        provider: str | None,
        auto_fetch_and_index: bool,
        llm_provider: str,
    ) -> dict[str, Any]:
        try:
            resp = requests.get(
                f"{self.base_url.rstrip('/')}/search",
                params={"q": query, "format": "json"},
                timeout=self.timeout_seconds,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logger.error("SearXNG enrichment search failed for %r: %s", query, exc)
            return {
                "query": query,
                "hits": [],
                "explanation": "",
                "provider": "searxng",
                "warnings": [f"SearXNG search failed: {exc}"],
            }

        hits: list[dict[str, Any]] = []
        for row in (data.get("results") or [])[: max(1, top_k)]:
            hits.append(
                {
                    "title": row.get("title") or "",
                    "url": row.get("url") or "",
                    "snippet": row.get("content") or "",
                    "score": row.get("score"),
                }
            )

        # Fall back to infoboxes/answers when the search engines are rate-limited
        # (they return an empty `results` list but often still yield a rich
        # Wikipedia/Wikidata infobox). This keeps enrichment from collapsing to
        # "limited_evidence" just because Google/Brave/DDG throttled SearXNG.
        for box in data.get("infoboxes") or []:
            content = box.get("content") or ""
            if not content:
                continue
            url = ""
            urls = box.get("urls") or []
            if urls and isinstance(urls[0], dict):
                url = urls[0].get("url") or ""
            hits.append(
                {
                    "title": box.get("infobox") or box.get("title") or "Overview",
                    "url": url or box.get("id") or "",
                    "snippet": content,
                    "score": 0.5,
                }
            )
        for answer in data.get("answers") or []:
            text = answer if isinstance(answer, str) else (answer.get("answer") if isinstance(answer, dict) else "")
            if text:
                hits.append({"title": "Answer", "url": "", "snippet": str(text), "score": 0.4})

        hits = hits[: max(1, top_k)]
        unresponsive = data.get("unresponsive_engines") or []
        logger.info(
            "SearXNG enrichment search ok: %s hits for %r (%d engines unresponsive)",
            len(hits), query, len(unresponsive),
        )
        return {"query": query, "hits": hits, "explanation": "", "provider": "searxng"}


@dataclass
class SerperSearchProvider:
    """Live web-search provider backed by Serper.dev (Google results as JSON).

    Primary enrichment search provider: real Google coverage with no CAPTCHA or
    scraping throttling. We keep ``num`` at 10 so each query costs 1 Serper credit.
    """

    api_key: str
    base_url: str = "https://google.serper.dev/search"
    timeout_seconds: float = 15.0
    name: str = "serper"

    def search(
        self,
        *,
        query: str,
        collection: str,
        top_k: int,
        provider: str | None,
        auto_fetch_and_index: bool,
        llm_provider: str,
    ) -> dict[str, Any]:
        try:
            resp = requests.post(
                self.base_url,
                json={"q": query, "num": min(max(int(top_k), 1), 10)},
                headers={"X-API-KEY": self.api_key, "Content-Type": "application/json"},
                timeout=self.timeout_seconds,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logger.error("Serper search failed for %r: %s", query, exc)
            return {
                "query": query,
                "hits": [],
                "explanation": "",
                "provider": "serper",
                "warnings": [f"Serper failed: {exc}"],
            }

        hits: list[dict[str, Any]] = []
        for row in (data.get("organic") or [])[: max(1, top_k)]:
            hits.append(
                {
                    "title": row.get("title") or "",
                    "url": row.get("link") or "",
                    "snippet": row.get("snippet") or "",
                    "score": row.get("position"),
                }
            )
        # Knowledge graph + answer box are high-value extra evidence.
        kg = data.get("knowledgeGraph") or {}
        if kg.get("description"):
            hits.append({
                "title": kg.get("title") or "Overview",
                "url": kg.get("descriptionLink") or kg.get("website") or "",
                "snippet": kg.get("description"),
                "score": 0.9,
            })
        ab = data.get("answerBox") or {}
        ab_text = ab.get("answer") or ab.get("snippet")
        if ab_text:
            hits.append({
                "title": ab.get("title") or "Answer",
                "url": ab.get("link") or "",
                "snippet": str(ab_text),
                "score": 0.8,
            })
        logger.info("Serper search ok: %s hits for %r", len(hits), query)
        return {"query": query, "hits": hits, "explanation": "", "provider": "serper"}


@dataclass
class FallbackSearchProvider:
    """Waterfall over search providers: try each in order, return the first that
    yields hits. Lets Serper be primary with SearXNG as a free fallback."""

    providers: list
    name: str = "fallback"

    def search(
        self,
        *,
        query: str,
        collection: str,
        top_k: int,
        provider: str | None,
        auto_fetch_and_index: bool,
        llm_provider: str,
    ) -> dict[str, Any]:
        kwargs = dict(
            query=query,
            collection=collection,
            top_k=top_k,
            provider=provider,
            auto_fetch_and_index=auto_fetch_and_index,
            llm_provider=llm_provider,
        )
        last: dict[str, Any] = {"query": query, "hits": [], "explanation": "", "provider": "none"}
        for p in self.providers:
            try:
                result = p.search(**kwargs)
            except Exception as exc:
                logger.error("Enrichment provider %s errored: %s", getattr(p, "name", p), exc)
                continue
            last = result
            if result.get("hits"):
                logger.info(
                    "Enrichment search served by %s (%d hits) for %r",
                    getattr(p, "name", "?"), len(result.get("hits") or []), query,
                )
                return result
        return last


@dataclass
class EnrichmentService:
    repository: EnrichmentRepository
    search_provider: SearchProvider | None = None
    llm_router: object | None = None

    @staticmethod
    def _is_fresh(ts: datetime | None) -> bool:
        if ts is None:
            return False
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        ttl = int(getattr(settings, "cache_ttl_days", 30))
        return (datetime.now(timezone.utc) - ts) < timedelta(days=ttl)

    def research(self, request: EnrichmentResearchRequest) -> EnrichmentResult:
        account = request.account
        account_id = account.account_id or self._slug_account(account)

        # Cache-first: reuse a fresh, complete enrichment instead of re-running
        # SearXNG + LLM. This is what stops repeat runs from re-hitting (and being
        # throttled by) the search engines for companies already researched.
        if getattr(settings, "enrichment_cache_enabled", True):
            cached = self.repository.get_latest(account_id)
            if cached and cached.status == "complete" and self._is_fresh(cached.updated_at):
                logger.info(
                    "Enrichment cache hit for %s (%s) - skipping web search",
                    account_id, account.company_name,
                )
                return cached

        provider = self.search_provider or NoopSearchProvider()
        collection = request.collection or settings.enrichment_collection
        top_k = request.top_k or settings.enrichment_top_k
        search_provider = request.search_provider or settings.enrichment_search_provider or None
        llm_provider = request.llm_provider or settings.enrichment_llm_provider

        queries = build_research_queries(request.account, request.contacts)
        search_runs: list[dict[str, Any]] = []
        all_hits: list[dict[str, Any]] = []
        explanations: list[str] = []

        for query in queries[:6]:
            result = provider.search(
                query=query,
                collection=collection,
                top_k=top_k,
                provider=search_provider,
                auto_fetch_and_index=request.auto_fetch_and_index,
                llm_provider=llm_provider,
            )
            search_runs.append(result)
            all_hits.extend(list(result.get("hits", []) or []))
            if result.get("explanation"):
                explanations.append(str(result.get("explanation")))

        unique_hits = self._dedupe_hits(all_hits)
        synthesis = self._synthesize(request, unique_hits, explanations)
        result = self._build_result(
            request=request,
            collection=collection,
            hits=unique_hits,
            search_runs=search_runs,
            synthesis=synthesis,
        )
        return self.repository.save(result)

    def get_latest(self, account_id: str) -> EnrichmentResult | None:
        return self.repository.get_latest(account_id)

    def list_results(self) -> list[EnrichmentResult]:
        return self.repository.list_latest()

    def _synthesize(
        self,
        request: EnrichmentResearchRequest,
        hits: list[dict[str, Any]],
        explanations: list[str],
    ) -> dict[str, Any]:
        if not self.llm_router:
            return {}
        prompt = self._build_synthesis_prompt(request, hits, explanations)
        raw = self.llm_router.complete(
            prompt=prompt,
            provider=request.llm_provider or settings.enrichment_llm_provider,
            max_tokens=1200,
            model_name=request.llm_model or settings.enrichment_llm_model,
        )
        return self._augment_synthesis(
            self._extract_json(raw),
            request=request,
            hits=hits,
            explanations=explanations,
        )

    def _build_result(
        self,
        *,
        request: EnrichmentResearchRequest,
        collection: str,
        hits: list[dict[str, Any]],
        search_runs: list[dict[str, Any]],
        synthesis: dict[str, Any],
    ) -> EnrichmentResult:
        account = request.account
        account_id = account.account_id or self._slug_account(account)
        citations = citations_from_hits(hits)
        fallback_summary = self._fallback_company_summary(account, hits)
        pain_points = self._coerce_list(synthesis.get("pain_point_hypotheses")) or self._fallback_pain_points(account)
        angles = self._coerce_list(synthesis.get("personalization_angles")) or self._fallback_angles(account, pain_points)
        signals = self._coerce_signals(synthesis.get("signals"), citations)
        confidence = self._coerce_float(synthesis.get("confidence_score"), default=0.55 if citations else 0.35)

        return EnrichmentResult(
            account_id=account_id,
            company_name=account.company_name,
            status="complete" if citations else "limited_evidence",
            collection=collection,
            company_summary=str(synthesis.get("company_summary") or fallback_summary),
            products_services=self._coerce_list(synthesis.get("products_services")),
            target_customers=self._coerce_list(synthesis.get("target_customers")),
            signals=signals,
            pain_point_hypotheses=pain_points,
            personalization_angles=angles,
            contact_briefs=self._contact_briefs(request),
            recommended_next_action=str(
                synthesis.get("recommended_next_action")
                or "Prioritize the most relevant revenue-facing contact and run personalized outreach using the cited signals."
            ),
            confidence_score=max(0.0, min(1.0, confidence)),
            citations=citations,
            raw_search={"queries": build_research_queries(account, request.contacts), "runs": search_runs[:6]},
            created_by=request.created_by,
        )

    def _build_synthesis_prompt(
        self,
        request: EnrichmentResearchRequest,
        hits: list[dict[str, Any]],
        explanations: list[str],
    ) -> str:
        payload = request.model_dump(mode="json")
        evidence = compact_evidence(hits)
        return (
            f"{ENRICHMENT_SYNTHESIS_PROMPT}\n\n"
            "Return valid JSON only with keys: company_summary, products_services, target_customers, "
            "signals, pain_point_hypotheses, personalization_angles, recommended_next_action, confidence_score.\n"
            "Signal schema: {\"type\":\"growth|hiring|product|news|intent|risk\", \"detail\":\"...\", "
            "\"confidence\":0.0, \"source_url\":\"...\"}.\n\n"
            "Requirements:\n"
            "- company_summary must be 2-4 sentences and commercially useful.\n"
            "- pain_point_hypotheses must contain at least 3 specific bullets when possible.\n"
            "- personalization_angles must contain at least 3 outreach angles tied to evidence.\n"
            "- recommended_next_action must be a concrete SDR next step, not generic advice.\n"
            "- Use hypotheses only when evidence is weak, and reflect that in confidence_score.\n\n"
            f"Account and contacts:\n{json.dumps(payload, indent=2)}\n\n"
            f"Search explanations:\n{json.dumps(explanations[:4], indent=2)}\n\n"
            f"Cited evidence:\n{evidence}\n"
        )

    def _augment_synthesis(
        self,
        synthesis: dict[str, Any],
        *,
        request: EnrichmentResearchRequest,
        hits: list[dict[str, Any]],
        explanations: list[str],
    ) -> dict[str, Any]:
        enriched = dict(synthesis or {})
        account = request.account
        evidence_titles = [
            str(hit.get("title") or hit.get("name") or "").strip()
            for hit in hits[:5]
            if str(hit.get("title") or hit.get("name") or "").strip()
        ]
        explanation_text = " ".join(explanations[:2]).strip()

        company_summary = str(enriched.get("company_summary") or "").strip()
        if not company_summary:
            summary_parts = [
                f"{account.company_name} appears to operate in {account.industry or 'its stated market'}"
            ]
            if account.location:
                summary_parts.append(f"with relevance in {account.location}")
            if evidence_titles:
                summary_parts.append(
                    "Public evidence reviewed includes "
                    + ", ".join(evidence_titles[:3])
                    + "."
                )
            else:
                summary_parts.append("The current enrichment run has limited public evidence.")
            if explanation_text:
                summary_parts.append(
                    "The evidence suggests there may be usable commercial context for SDR outreach."
                )
            enriched["company_summary"] = " ".join(summary_parts)

        products_services = self._coerce_list(enriched.get("products_services"))
        if not products_services and evidence_titles:
            products_services = evidence_titles[:3]
        enriched["products_services"] = products_services

        target_customers = self._coerce_list(enriched.get("target_customers"))
        if not target_customers and request.icp_context:
            target_customers = self._coerce_list(
                request.icp_context.get("persona_criteria", {}).get("titles")
                or request.icp_context.get("pain_points")
            )[:3]
        enriched["target_customers"] = target_customers

        pain_points = self._coerce_list(enriched.get("pain_point_hypotheses"))
        fallback_pain_points = self._fallback_pain_points(account)
        for item in fallback_pain_points:
            if item not in pain_points:
                pain_points.append(item)
        icp_pain_points = self._coerce_list(
            request.icp_context.get("pain_points") if request.icp_context else []
        )
        for item in icp_pain_points:
            if item not in pain_points:
                pain_points.append(item)
        enriched["pain_point_hypotheses"] = pain_points[:4]

        angles = self._coerce_list(enriched.get("personalization_angles"))
        for item in self._fallback_angles(account, enriched["pain_point_hypotheses"]):
            if item not in angles:
                angles.append(item)
        if evidence_titles:
            title_angle = f"Reference evidence such as {evidence_titles[0]} to make the first outreach line specific."
            if title_angle not in angles:
                angles.append(title_angle)
        enriched["personalization_angles"] = angles[:4]

        next_action = str(enriched.get("recommended_next_action") or "").strip()
        if len(next_action) < 30:
            enriched["recommended_next_action"] = (
                f"Prioritize outreach to the strongest matching contact at {account.company_name}, "
                "lead with one cited operational signal, and test a message tied to the top inferred pain point."
            )

        if enriched.get("confidence_score") in (None, ""):
            enriched["confidence_score"] = 0.7 if hits else 0.4

        return enriched

    @staticmethod
    def _extract_json(raw: str) -> dict[str, Any]:
        raw = str(raw or "").strip()
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return {}
        try:
            data = json.loads(raw[start : end + 1])
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    @staticmethod
    def _dedupe_hits(hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[str] = set()
        out: list[dict[str, Any]] = []
        for hit in hits:
            key = str(hit.get("url") or hit.get("source_url") or hit.get("title") or hit)
            if key in seen:
                continue
            seen.add(key)
            out.append(hit)
        return out

    @staticmethod
    def _slug_account(account: EnrichmentAccount) -> str:
        return "".join(ch.lower() if ch.isalnum() else "_" for ch in account.company_name).strip("_") or "account"

    @staticmethod
    def _fallback_company_summary(account: EnrichmentAccount, hits: list[dict[str, Any]]) -> str:
        base = f"{account.company_name} is a target account"
        if account.industry:
            base += f" in {account.industry}"
        if account.location:
            base += f" with relevance in {account.location}"
        if hits:
            base += ". Public web evidence was collected, so this account can be positioned with more specific outreach."
        else:
            base += ". No strong web evidence was retrieved yet, so the brief should be treated as an early hypothesis."
        return base

    @staticmethod
    def _fallback_pain_points(account: EnrichmentAccount) -> list[str]:
        if account.industry and "fitness" in account.industry.lower():
            return ["lead follow-up friction", "quote qualification gaps", "financing journey drop-off"]
        if account.industry and any(token in account.industry.lower() for token in ["saas", "software", "fintech"]):
            return ["pipeline visibility gaps", "forecasting inconsistency", "manual lead routing friction"]
        return ["manual prospect research", "low personalization quality", "slow lead qualification"]

    @staticmethod
    def _fallback_angles(account: EnrichmentAccount, pain_points: list[str]) -> list[str]:
        return [
            f"Reference {account.company_name}'s market context and connect it to {pain_points[0]}.",
            "Lead with a specific operational pain point rather than a generic AI pitch.",
            "Anchor outreach on one commercial signal and one practical outcome the target persona likely owns.",
        ]

    @staticmethod
    def _contact_briefs(request: EnrichmentResearchRequest) -> list[dict[str, Any]]:
        briefs: list[dict[str, Any]] = []
        for contact in request.contacts:
            likely_responsibility = f"Owns outcomes related to {contact.department or contact.title or 'the buying committee'}."
            if contact.title and "sales" in contact.title.lower():
                likely_responsibility = "Likely owns pipeline quality, conversion, and forecast accountability."
            elif contact.title and any(token in contact.title.lower() for token in ["revops", "operations"]):
                likely_responsibility = "Likely owns process efficiency, routing quality, and revenue operations visibility."
            briefs.append(
                {
                    "contact_id": contact.contact_id,
                    "full_name": contact.full_name,
                    "title": contact.title,
                    "likely_responsibility": likely_responsibility,
                    "personalization_hook": (
                        f"Connect outreach to {request.account.company_name}'s current account signals "
                        "and the likely KPI pressure this contact owns."
                    ),
                }
            )
        return briefs

    @classmethod
    def _coerce_signals(cls, value: Any, citations: list[Any]) -> list[EnrichmentSignal]:
        signals: list[EnrichmentSignal] = []
        if isinstance(value, list):
            for item in value:
                if not isinstance(item, dict):
                    continue
                detail = str(item.get("detail") or "").strip()
                if not detail:
                    continue
                signals.append(
                    EnrichmentSignal(
                        type=str(item.get("type") or "research"),
                        detail=detail,
                        confidence=cls._coerce_float(item.get("confidence"), 0.5),
                        source_url=str(item.get("source_url") or "") or None,
                    )
                )
        if not signals and citations:
            first = citations[0]
            signals.append(
                EnrichmentSignal(
                    type="research_evidence",
                    detail=f"Relevant public evidence found: {first.title or first.url}",
                    confidence=0.55,
                    source_url=first.url or None,
                )
            )
        return signals

    @staticmethod
    def _coerce_list(value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value] if value.strip() else []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return []

    @staticmethod
    def _coerce_float(value: Any, default: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default
