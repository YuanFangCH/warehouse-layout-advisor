import threading
from datetime import datetime, timezone


class EventPublisher:
    """In-memory event bus used by the SSE evaluation stream."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._events: dict[str, list[dict]] = {}
        self._counter = 0

    def publish(self, evaluation_id: str, event: dict) -> None:
        with self._lock:
            self._counter += 1
            item = {
                **event,
                "seq": self._counter,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            self._events.setdefault(evaluation_id, []).append(item)

    def events_since(self, evaluation_id: str, after_seq: int = 0) -> list[dict]:
        with self._lock:
            return [event for event in self._events.get(evaluation_id, []) if event["seq"] > after_seq]


publisher = EventPublisher()
