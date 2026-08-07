from __future__ import annotations

import logging
import os
from typing import Any
import requests

from ai_sdr_platform.src.shared.config import settings

logger = logging.getLogger("sdr.infra.llm")


class LLMUnavailable(Exception):
    """Raised when configured LLM provider fails or is unreachable."""
    pass


class MultiProviderLLMClient:
    """
    Unified LLM provider client supporting xAI Grok, Groq, Ollama, and OpenAI-compatible endpoints.
    Encapsulates smart key detection, provider routing, and fallback execution.
    """

    def __init__(
        self,
        grok_api_key: str | None = None,
        groq_api_key: str | None = None,
        grok_model: str | None = None,
        groq_model: str | None = None,
        ollama_base_url: str | None = None,
        ollama_model: str | None = None,
    ):
        grok_key = (grok_api_key or settings.grok_api_key or os.getenv("GROK_API_KEY", "")).strip()
        groq_key = (groq_api_key or settings.groq_api_key or os.getenv("GROQ_API_KEY", "")).strip()

        # Smart key routing: if a key starting with 'gsk_' is in GROK_API_KEY, treat it as a Groq key
        if grok_key.startswith("gsk_") and not groq_key:
            groq_key = grok_key
            grok_key = ""

        if grok_key:
            self.provider_name = "xAI Grok"
            self.api_key = grok_key
            self.model = grok_model or settings.grok_model or "grok-beta"
            self.api_url = "https://api.x.ai/v1/chat/completions"
            self.mode = "openai_http"
        elif groq_key:
            self.provider_name = "Groq LLM"
            self.api_key = groq_key
            self.model = groq_model or settings.groq_model or "llama-3.3-70b-versatile"
            self.api_url = "https://api.groq.com/openai/v1/chat/completions"
            self.mode = "openai_http"
        else:
            self.provider_name = "Ollama Local"
            self.api_key = ""
            self.model = ollama_model or settings.conversation_llm_model or "llama3.1:8b"
            self.api_url = (ollama_base_url or settings.conversation_llm_base_url or "http://127.0.0.1:11434").rstrip("/")
            self.mode = "ollama"

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 800,
        timeout: float = 30.0,
    ) -> str:
        """Generate text completion using the active provider."""
        if self.mode == "openai_http":
            return self._openai_chat_completion(system_prompt, user_prompt, temperature, max_tokens, timeout)
        else:
            return self._ollama_chat_completion(system_prompt, user_prompt, temperature, max_tokens, timeout)

    def _openai_chat_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
        timeout: float,
    ) -> str:
        if not self.api_key:
            raise LLMUnavailable(f"No API key configured for {self.provider_name}.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        try:
            resp = requests.post(self.api_url, headers=headers, json=payload, timeout=timeout)
        except Exception as exc:
            raise LLMUnavailable(f"{self.provider_name} request failed: {exc}") from exc

        if not resp.ok:
            raise LLMUnavailable(f"{self.provider_name} error HTTP {resp.status_code}: {resp.text}")

        try:
            return resp.json()["choices"][0]["message"]["content"].strip()
        except Exception as exc:
            raise LLMUnavailable(f"Unexpected {self.provider_name} response format: {exc}") from exc

    def _ollama_chat_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
        timeout: float,
    ) -> str:
        payload = {
            "model": self.model,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        try:
            resp = requests.post(f"{self.api_url}/api/chat", json=payload, timeout=timeout)
        except Exception as exc:
            raise LLMUnavailable(f"Ollama local request failed at {self.api_url}: {exc}") from exc

        if not resp.ok:
            raise LLMUnavailable(f"Ollama local error HTTP {resp.status_code}: {resp.text}")

        try:
            return resp.json()["message"]["content"].strip()
        except Exception as exc:
            raise LLMUnavailable(f"Unexpected Ollama response format: {exc}") from exc
