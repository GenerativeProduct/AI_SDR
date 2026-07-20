from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from dataclasses import dataclass
from time import perf_counter
from typing import Any, Iterator
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass
class ConversationObservation:
    trace_id: str
    span: Any | None = None
    output: Any = None

    def finish(self, *, output: Any = None, error: Exception | None = None) -> None:
        if output is not None:
            self.output = output
        if self.span is None:
            return
        self.span.update(
            output=self.output,
            level="ERROR" if error else "DEFAULT",
            status_message=str(error) if error else None,
        )
        self.span.end()


class ConversationObservability:
    def __init__(self) -> None:
        self.langfuse_configured = bool(
            os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY")
        )
        self._client = None
        if self.langfuse_configured:
            try:
                from langfuse import get_client

                self._client = get_client()
            except Exception:
                logger.exception("conversation.langfuse initialization failed")

    @contextmanager
    def trace(
        self,
        operation: str,
        *,
        input_data: Any,
        metadata: dict[str, Any] | None = None,
    ) -> Iterator[ConversationObservation]:
        started = perf_counter()
        span = None
        trace_id = str(uuid4())
        if self._client is not None:
            try:
                span = self._client.start_observation(
                    name=f"conversation.{operation}",
                    as_type="agent",
                    input=input_data,
                    metadata=metadata or {},
                )
                trace_id = getattr(span, "trace_id", trace_id)
            except Exception:
                logger.exception("conversation.langfuse trace start failed")
        observation = ConversationObservation(trace_id=trace_id, span=span)
        error = None
        try:
            yield observation
        except Exception as exc:
            error = exc
            raise
        finally:
            observation.finish(error=error)
            logger.info(
                "conversation.%s trace_id=%s duration_ms=%.2f metadata=%s",
                operation,
                trace_id,
                (perf_counter() - started) * 1000,
                metadata or {},
            )

    def flush(self) -> None:
        if self._client is not None:
            self._client.flush()
