import datetime
import uuid
from typing import Any, Dict
import contextvars

# Context variable for propagating event context.
current_event_context = contextvars.ContextVar("current_event_context", default={})

class Event:
    """
    Represents an event with a name, payload, metadata, and cancellation support.
    """
    def __init__(self, name: str, payload: Dict[str, Any] = None, metadata: Dict[str, Any] = None):
        self.name = name
        self.payload = payload or {}
        self.metadata = metadata or {}
        # Automatically set a timestamp.
        self.metadata.setdefault("timestamp", datetime.datetime.utcnow().isoformat())
        # Ensure each event has a correlation id for tracing.
        self.metadata.setdefault("correlation_id", str(uuid.uuid4()))
        # Flag to allow listeners to cancel propagation.
        self.cancelled = False

    def cancel(self):
        """Cancel further propagation of this event."""
        self.cancelled = True

    def __repr__(self):
        return (f"<Event name={self.name} payload={self.payload} "
                f"metadata={self.metadata} cancelled={self.cancelled}>")
