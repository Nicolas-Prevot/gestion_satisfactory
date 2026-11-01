from collections import OrderedDict
from threading import Lock
from typing import Any


class ErrorRegistry:
    def __init__(self, max_entries: int = 300) -> None:
        self.max_entries = max_entries
        self._errors: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self._lock = Lock()

    def store(self, trace_id: str, payload: dict[str, Any]) -> None:
        with self._lock:
            self._errors[trace_id] = payload
            while len(self._errors) > self.max_entries:
                self._errors.popitem(last=False)

    def get(self, trace_id: str) -> dict[str, Any] | None:
        with self._lock:
            return self._errors.get(trace_id)


error_registry = ErrorRegistry()
