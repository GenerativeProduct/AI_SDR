"""Minimal local LLM router backed by Ollama.

The enrichment, personalization, ICP-suggestion and outreach agents all call an
injected object with a ``.complete(prompt=..., provider=..., max_tokens=...,
model_name=...)`` method. The original implementation lived in a separate
``backend/`` package that isn't present in this repo, so ``llm_router`` was
always ``None`` and every "LLM" step silently fell back to templates/heuristics.

This class provides that interface by talking to a local Ollama server, so all
of those agents produce real model output.
"""

from __future__ import annotations

import logging

import requests

from ai_sdr_platform.src.shared.config import settings

logger = logging.getLogger("sdr.llm")


class OllamaLLMRouter:
    def __init__(self, base_url: str | None = None, timeout_seconds: float | None = None) -> None:
        self.base_url = (base_url or settings.llm_base_url).rstrip("/")
        self.timeout_seconds = timeout_seconds or settings.llm_timeout_seconds

    def complete(
        self,
        prompt: str = "",
        provider: str | None = None,
        max_tokens: int = 800,
        model_name: str | None = None,
        **_ignored,
    ) -> str:
        """Return the model's text completion for a single prompt. On any failure
        returns an empty string so callers cleanly fall back to their templates."""
        model = model_name or settings.enrichment_llm_model or "llama3.2:3b"
        try:
            resp = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_predict": int(max_tokens)},
                },
                timeout=self.timeout_seconds,
            )
            resp.raise_for_status()
            text = str((resp.json() or {}).get("response") or "").strip()
            if not text:
                logger.warning("Ollama returned empty response (model=%s)", model)
            return text
        except Exception as exc:
            logger.error("Ollama complete failed (model=%s @ %s): %s", model, self.base_url, exc)
            return ""
