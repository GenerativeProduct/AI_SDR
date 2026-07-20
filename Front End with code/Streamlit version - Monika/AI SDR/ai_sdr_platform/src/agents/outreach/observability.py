from __future__ import annotations

import logging
from contextlib import contextmanager
from time import perf_counter
from typing import Iterator

logger = logging.getLogger(__name__)


class OutreachObservability:
    @contextmanager
    def span(self, operation: str, **attributes: object) -> Iterator[None]:
        start = perf_counter()
        try:
            yield
        except Exception:
            logger.exception("outreach.%s failed attributes=%s", operation, attributes)
            raise
        finally:
            logger.info(
                "outreach.%s duration_ms=%.2f attributes=%s",
                operation,
                (perf_counter() - start) * 1000,
                attributes,
            )
