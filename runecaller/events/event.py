import datetime
import uuid
from typing import Any, Dict, Optional, List
import contextvars
from bedrocked.reporting.reported import logger


EVENT_GROUPS = {
    "auth_events": ["user_login", "user_logout", "password_reset"],
    "system_health": ["system_start", "system_shutdown", "error_occurred"],
    "data_changes": ["record_created", "record_updated", "record_deleted"],
}

class EventMetadata:
    def __init__(
        self,
        event_name: str,
        event_type: str,
        tags: Optional[List[str]] = None,
        group: Optional[str] = None,
        priority: int = 1,
        timestamp: Optional[datetime] = None,
        source: Optional[str] = None,
        initiator: Optional[str] = None,
        payload_schema: Optional[Dict] = None,
        execution_mode: str = "sync",  # Options: sync, async, deferred
        retry_policy: Optional[Dict] = None,
        persisted: bool = False,
        expiration: Optional[datetime] = None,
        dependencies: Optional[List[str]] = None,
        allowed_handlers: Optional[List[str]] = None,
        confidentiality: str = "public",  # Options: public, private, classified
        audit_required: bool = False,
        access_roles: Optional[List[str]] = None,
        signature: Optional[str] = None,
        trace_id: Optional[str] = None,
        execution_time: Optional[float] = None,
        resource_usage: Optional[Dict] = None,
        error_count: int = 0,
        status: str = "pending",  # pending, processing, completed, failed
        last_attempt: Optional[datetime] = None,
    ):
        self.event_name = event_name
        self.event_type = event_type
        self.tags = tags or []
        self.group = group
        self.priority = priority
        self.timestamp = timestamp or datetime.datetime.now()
        self.source = source
        self.initiator = initiator
        self.payload_schema = payload_schema
        self.execution_mode = execution_mode
        self.retry_policy = retry_policy or {"max_attempts": 3, "backoff_time": 2}  # Default retry config
        self.persisted = persisted
        self.expiration = expiration
        self.dependencies = dependencies or []
        self.allowed_handlers = allowed_handlers
        self.confidentiality = confidentiality
        self.audit_required = audit_required
        self.access_roles = access_roles
        self.signature = signature
        self.trace_id = trace_id
        self.execution_time = execution_time
        self.resource_usage = resource_usage or {}
        self.error_count = error_count
        self.status = status
        self.last_attempt = last_attempt

    def __repr__(self):
        return f"<EventMetadata {self.event_name} [{self.event_type}] priority={self.priority}>"



# Context variable for propagating event context.
current_event_context = contextvars.ContextVar("current_event_context", default={})

class Event:
    """
    Represents an event with a name, payload, metadata, and cancellation support.
    """
    def __init__(self, name: str, payload: Dict[str, Any] = None, metadata: Dict[str, Any] = None, context: dict = None):
        self.name = name
        self.payload = payload or {}
        self.metadata = metadata or {}
        # Automatically set a timestamp.
        self.metadata.setdefault("timestamp", datetime.datetime.now().isoformat())
        # Ensure each event has a correlation id for tracing.
        self.metadata.setdefault("correlation_id", str(uuid.uuid4()))
        self.metadata.setdefault("")
        # Unified context that can be passed along and updated.
        self.context = context or {}
        # Optionally, initialize context with metadata if needed.
        self.context.setdefault("initial_timestamp", self.metadata["timestamp"])

        # Flag to allow listeners to cancel propagation.
        self.cancelled = False

    def cancel(self):
        """Cancel further propagation of this event."""
        self.cancelled = True

    def __repr__(self):
        return (f"<Event name={self.name} payload={self.payload} "
                f"metadata={self.metadata} context={self.context} cancelled={self.cancelled}>")


if __name__ == '__main__':
# Example hook function
    def sample_hook(event):
        # Access unified context
        print("Before hook, context:", event.context)
        # Update the context
        event.context["hook_executed"] = True
        print("After hook, context:", event.context)

        return "hook_result"

    event = Event("app.reboot.scheduled")
    boo = sample_hook(event)
    print(event)