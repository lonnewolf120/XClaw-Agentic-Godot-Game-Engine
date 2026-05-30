from __future__ import annotations

from collections import deque
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Deque, Dict, List, Optional


@dataclass
class ActivityEvent:
    timestamp: str
    level: str
    source: str
    event_type: str
    message: str
    details: Dict[str, Any]


class ActivityMonitor:
    def __init__(self, max_events: int = 2000) -> None:
        self._events: Deque[ActivityEvent] = deque(maxlen=max_events)
        self._lock = Lock()

    def record(
        self,
        *,
        level: str,
        source: str,
        event_type: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        event = ActivityEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            level=level,
            source=source,
            event_type=event_type,
            message=message,
            details=details or {},
        )
        with self._lock:
            self._events.append(event)

    def list_events(self, *, limit: int = 200, source: Optional[str] = None, level: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            items = list(self._events)

        if source:
            items = [e for e in items if e.source == source]
        if level:
            items = [e for e in items if e.level == level]

        items = items[-max(1, min(limit, 2000)) :]
        return [asdict(e) for e in items]


activity_monitor = ActivityMonitor()
