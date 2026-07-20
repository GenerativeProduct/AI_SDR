from __future__ import annotations

import json
from dataclasses import dataclass

from ai_sdr_platform.src.agents.icp.models import ExclusionCriteria, ICPSuggestionRequest, ICPSuggestionResponse
from ai_sdr_platform.src.agents.icp.prompts import ICP_SUGGESTION_SYSTEM_PROMPT


@dataclass
class LLMSuggestionProvider:
    llm_router: object

    def suggest(self, request: ICPSuggestionRequest) -> ICPSuggestionResponse:
        prompt = self._build_prompt(request)
        raw = self.llm_router.complete(
            prompt=prompt,
            provider="ollama_local" if request.llm_provider == "auto" else request.llm_provider,
            max_tokens=400,
            model_name=request.model_name,
        )
        data = self._extract_json(raw)
        exclusions = self._coerce_exclusions(data.get("exclusions", {}))
        personas = self._coerce_list(data.get("personas", []))
        pain_points = self._coerce_list(data.get("pain_points", []))
        reasoning = self._clean_reasoning(
            str(data.get("reasoning") or "").strip(),
            request=request,
            personas=personas,
            pain_points=pain_points,
        )
        return ICPSuggestionResponse(
            personas=personas,
            pain_points=pain_points,
            exclusions=exclusions,
            reasoning=reasoning,
            source="llm",
        )

    def _build_prompt(self, request: ICPSuggestionRequest) -> str:
        payload = request.model_dump(mode="json", exclude_none=True)
        context_parts: list[str] = []
        if request.prompt:
            context_parts.append(f"USER PROMPT: {request.prompt}")
        if request.filters:
            context_parts.append(
                "STRUCTURED FILTERS: "
                + json.dumps(request.filters.model_dump(exclude_none=True), indent=2)
            )
        context = "\n\n".join(context_parts)
        return (
            f"{ICP_SUGGESTION_SYSTEM_PROMPT}\n\n"
            "Return valid JSON only with keys: personas, pain_points, exclusions, reasoning.\n"
            "Schema:\n"
            "{\n"
            '  "personas": ["VP Sales"],\n'
            '  "pain_points": ["poor pipeline visibility"],\n'
            '  "exclusions": {\n'
            '    "industries": [],\n'
            '    "customer_statuses": ["existing_customer"],\n'
            '    "company_names": [],\n'
            '    "employee_max_below": 20,\n'
            '    "geographies": []\n'
            "  },\n"
            '  "reasoning": "Explain why these personas and pain points are commercially relevant. Do not repeat the input text."\n'
            "}\n"
            "Keep suggestions practical and conservative.\n"
            "Treat structured filters as hard constraints and use the prompt for refinement.\n"
            "The reasoning must be 1-2 business sentences and must not copy or restate the user's notes.\n\n"
            f"INPUT CONTEXT:\n{context}\n\n"
            f"FULL PAYLOAD:\n{json.dumps(payload, indent=2)}"
        )

    @classmethod
    def _clean_reasoning(
        cls,
        reasoning: str,
        *,
        request: ICPSuggestionRequest,
        personas: list[str],
        pain_points: list[str],
    ) -> str:
        notes = (request.notes or "").strip()
        weak_reasoning = (
            not reasoning
            or reasoning.lower() in {"short explanation", "llm suggested icp refinements."}
            or (notes and reasoning.lower() == notes.lower())
            or (notes and notes.lower() in reasoning.lower() and len(reasoning) <= len(notes) + 20)
        )
        if not weak_reasoning:
            return reasoning

        industries = cls._join_or_default(request.industries, "the selected industries")
        geographies = cls._join_or_default(request.geographies, "the selected markets")
        persona_text = cls._join_or_default(personas or request.target_personas, "revenue-facing decision makers")
        pain_text = cls._join_or_default(pain_points or request.pain_points, "the stated go-to-market pain points")
        return (
            f"{persona_text} are strong ICP personas because they directly own pipeline quality, conversion, "
            f"and revenue execution for {industries} accounts in {geographies}. "
            f"The selected pain points ({pain_text}) indicate clear urgency and give downstream SDR agents "
            "specific angles for account discovery, scoring, and personalized outreach."
        )

    @staticmethod
    def _join_or_default(values: list[str], default: str) -> str:
        cleaned = [str(value).strip() for value in values if str(value).strip()]
        if not cleaned:
            return default
        return ", ".join(cleaned[:5])

    @staticmethod
    def _coerce_list(value: object) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value] if value.strip() else []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return []

    @classmethod
    def _coerce_exclusions(cls, value: object) -> ExclusionCriteria:
        if not isinstance(value, dict):
            return ExclusionCriteria(customer_statuses=["existing_customer"], employee_max_below=20)

        employee_max_below = value.get("employee_max_below", 20)
        try:
            employee_max_below = int(employee_max_below) if employee_max_below is not None else None
        except (TypeError, ValueError):
            employee_max_below = 20

        return ExclusionCriteria(
            industries=cls._coerce_list(value.get("industries", [])),
            customer_statuses=cls._coerce_list(value.get("customer_statuses", ["existing_customer"])),
            company_names=cls._coerce_list(value.get("company_names", [])),
            employee_max_below=employee_max_below,
            geographies=cls._coerce_list(value.get("geographies", [])),
        )

    @staticmethod
    def _extract_json(raw: str) -> dict:
        raw = raw.strip()
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return {
                "personas": [],
                "pain_points": [],
                "exclusions": {},
                "reasoning": "LLM response was unavailable or not parseable.",
            }
        try:
            return json.loads(raw[start : end + 1])
        except Exception:
            return {
                "personas": [],
                "pain_points": [],
                "exclusions": {},
                "reasoning": "LLM response could not be parsed into structured JSON.",
            }
