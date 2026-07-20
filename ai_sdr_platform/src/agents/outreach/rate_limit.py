from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from threading import Lock


@dataclass
class OutreachRateLimiter:
    max_per_minute: int = 30
    max_per_recipient_per_day: int = 3
    _global: deque[datetime] = field(default_factory=deque)
    _recipients: dict[str, deque[datetime]] = field(default_factory=lambda: defaultdict(deque))
    _lock: Lock = field(default_factory=Lock)

    def acquire(self, recipient: str) -> tuple[bool, str | None]:
        now = datetime.now(timezone.utc)
        with self._lock:
            self._trim(self._global, now - timedelta(minutes=1))
            recipient_events = self._recipients[recipient]
            self._trim(recipient_events, now - timedelta(days=1))
            if len(self._global) >= self.max_per_minute:
                return False, "Global outreach rate limit reached."
            if len(recipient_events) >= self.max_per_recipient_per_day:
                return False, "Recipient frequency limit reached."
            self._global.append(now)
            recipient_events.append(now)
        return True, None

    @staticmethod
    def _trim(events: deque[datetime], threshold: datetime) -> None:
        while events and events[0] < threshold:
            events.popleft()
