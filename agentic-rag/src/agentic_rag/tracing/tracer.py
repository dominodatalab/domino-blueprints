# tracer.py
"""Simple tracing for observability."""

import time
import uuid
from dataclasses import dataclass, field
from typing import Any
from datetime import datetime


@dataclass
class TraceSpan:
    """A single span in a trace."""
    name: str
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)

    def end(self):
        """End the span."""
        self.end_time = time.time()

    @property
    def duration_ms(self) -> float | None:
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return None

    def add_event(self, name: str, attributes: dict[str, Any] | None = None):
        """Add an event to the span."""
        self.events.append({
            "name": name,
            "timestamp": time.time(),
            "attributes": attributes or {},
        })

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "attributes": self.attributes,
            "events": self.events,
        }


class Tracer:
    """Simple tracer for request tracing."""

    def __init__(self):
        self.trace_id = str(uuid.uuid4())
        self.spans: list[TraceSpan] = []
        self.start_time = time.time()

    def start_span(self, name: str, attributes: dict[str, Any] | None = None) -> TraceSpan:
        """Start a new span."""
        span = TraceSpan(name=name, attributes=attributes or {})
        self.spans.append(span)
        return span

    def to_dict(self) -> dict:
        return {
            "trace_id": self.trace_id,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "total_duration_ms": (time.time() - self.start_time) * 1000,
            "spans": [span.to_dict() for span in self.spans],
        }

    def export_json(self) -> str:
        """Export trace as JSON string."""
        import json
        return json.dumps(self.to_dict(), indent=2)
