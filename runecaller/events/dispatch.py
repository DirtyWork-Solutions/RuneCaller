import asyncio
import time
import logging
from typing import Any, Callable, Dict, List, Tuple, Union
from runecaller.events.event import Event, current_event_context
from .schema import EventSchema
from runecaller.events.enhancements import (
    global_load_monitor,
    global_circuit_breaker,
    global_logging_config,
    alert_event
)

logger = logging.getLogger(__name__)

# Middleware: functions that modify or log events before dispatch.
middleware: List[Callable[[Event], Event]] = []

def add_middleware(fn: Callable[[Event], Event]):
    """Register a middleware function for events."""
    middleware.append(fn)

# Listener registries remain the same as before (with advanced filtering already implemented)
_listener_registry: Dict[str, List[Tuple[int, Callable[[Event], Any], Callable[[Event], bool]]]] = {}
_wildcard_registry: List[Tuple[str, int, Callable[[Event], Any], Callable[[Event], bool]]] = []

def register_listener(event_pattern: str, listener: Callable[[Event], Any], priority: int = 10, predicate: Callable[[Event], bool] = lambda e: True):
    """
    Subscribe a listener to an event pattern with an optional predicate filter.
    """
    if '*' in event_pattern:
        _wildcard_registry.append((event_pattern, priority, listener, predicate))
    else:
        _listener_registry.setdefault(event_pattern, []).append((priority, listener, predicate))
        _listener_registry[event_pattern].sort(key=lambda tup: tup[0])

def unregister_listener(event_pattern: str, listener: Callable[[Event], Any]):
    """Unsubscribe a listener from an event."""
    if '*' in event_pattern:
        global _wildcard_registry
        _wildcard_registry = [
            (pat, prio, l, pred) for pat, prio, l, pred in _wildcard_registry
            if not (pat == event_pattern and l == listener)
        ]
    else:
        if event_pattern in _listener_registry:
            _listener_registry[event_pattern] = [
                (prio, l, pred) for prio, l, pred in _listener_registry[event_pattern] if l != listener
            ]

def get_listeners(event: Event) -> List[Callable[[Event], Any]]:
    """
    Retrieve all listeners for an event, including exact and wildcard matches,
    applying predicate filtering and sorting by priority.
    """
    listeners: List[Tuple[int, Callable[[Event], Any]]] = []
    for tup in _listener_registry.get(event.name, []):
        priority, listener, predicate = tup
        if predicate(event):
            listeners.append((priority, listener))
    for pattern, prio, listener, predicate in _wildcard_registry:
        if pattern.endswith('*'):
            prefix = pattern[:-1]
            if event.name.startswith(prefix) and predicate(event):
                listeners.append((prio, listener))
    listeners.sort(key=lambda tup: tup[0])
    return [listener for _, listener in listeners]

def forward_event_to_bus(event: Event):
    """
    Stub for external message bus integration.
    """
    logger.info(f"Forwarding event {event.name} to external message bus (Correlation ID: {event.metadata.get('correlation_id')})")

def validate_event(event: Event) -> Event:
    """
    Validate an event using a Pydantic schema.
    """
    validated = EventSchema(name=event.name, payload=event.payload, metadata=event.metadata)
    return event

def dispatch(event: Union[Event, str], payload: Dict[str, Any] = None, mode: str = 'sync'):
    """
    Dispatch an event with integrated advanced features:
      - Dynamic load adaptation
      - Circuit breaker checks
      - Lifecycle hooks and fine-grained logging & alerting
    """
    # Step 1: Convert to Event if necessary and validate.
    if isinstance(event, str):
        event_obj = Event(name=event, payload=payload)
    else:
        event_obj = event

    try:
        event_obj = validate_event(event_obj)
    except Exception as e:
        logger.exception(f"Event validation failed: {e}")
        return

    # Step 2: Rate limiting (already handled by previous code) and now record the event for load monitoring.
    global_load_monitor.record_event()
    if global_load_monitor.is_high_load():
        logger.warning(f"High load detected; forcing event {event_obj.name} into 'deferred' mode.")
        mode = 'deferred'

    # Step 3: Circuit Breaker Check
    if not global_circuit_breaker.allow_event(event_obj.name):
        alert_event(event_obj.name, "Circuit breaker tripped – event dispatch halted.")
        return

    # Step 4: Set context propagation.
    token = current_event_context.set(event_obj.metadata)

    # Step 5: Apply middleware.
    for fn in middleware:
        event_obj = fn(event_obj)

    # Step 6: Persist event and forward externally.
    # (Assumes persistence and forwarding are handled in separate modules; code omitted here for brevity.)
    # persist_event(event_obj)  # If persistence is enabled
    forward_event_to_bus(event_obj)

    start_time = time.time()
    listeners = get_listeners(event_obj)

    try:
        if mode == 'sync':
            for listener in listeners:
                if event_obj.cancelled:
                    logger.debug(f"Event {event_obj.name} cancelled; stopping propagation.")
                    break
                try:
                    listener(event_obj)
                except Exception as listener_err:
                    logger.exception(f"Error in listener {listener} for event {event_obj.name}: {listener_err}")
                    global_circuit_breaker.record_failure(event_obj.name)
                    alert_event(event_obj.name, f"Listener failure: {listener_err}")
        elif mode == 'async':
            loop = asyncio.get_event_loop()
            for listener in listeners:
                if event_obj.cancelled:
                    logger.debug(f"Event {event_obj.name} cancelled; stopping propagation.")
                    break
                loop.create_task(async_listener_wrapper(listener, event_obj))
        elif mode == 'deferred':
            logger.debug(f"Deferred dispatch for event {event_obj.name} with payload {event_obj.payload}")
        else:
            raise ValueError("Invalid dispatch mode. Choose 'sync', 'async', or 'deferred'.")
    except Exception as dispatch_error:
        logger.exception(f"Dispatch error for event {event_obj.name}: {dispatch_error}")
        global_circuit_breaker.record_failure(event_obj.name)
        alert_event(event_obj.name, f"Dispatch error: {dispatch_error}")
    finally:
        elapsed = time.time() - start_time
        logger.info(f"Dispatched event {event_obj.name} in {elapsed:.4f} seconds.")
        current_event_context.reset(token)

async def async_listener_wrapper(listener: Callable[[Event], Any], event: Event):
    try:
        result = listener(event)
        if asyncio.iscoroutine(result):
            await result
    except Exception as e:
        logger.exception(f"Error in async listener {listener} for event {event.name}: {e}")
        global_circuit_breaker.record_failure(event.name)
        alert_event(event.name, f"Async listener failure: {e}")
