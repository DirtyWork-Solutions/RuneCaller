import asyncio
import time
import logging
from typing import Any, Callable, Dict, List, Tuple, Union
from .event import Event, current_event_context
from .schema import EventSchema
from .enhancements import (
    global_rate_limiter,
    persist_event,
    before_dispatch_hooks,
    after_dispatch_hooks,
    on_error_hooks
)

logger = logging.getLogger(__name__)

# Middleware: functions that modify or log events before dispatch.
middleware: List[Callable[[Event], Event]] = []


def add_middleware(fn: Callable[[Event], Event]):
    """Register a middleware function for events."""
    middleware.append(fn)


# Listener registry now supports advanced filtering via an optional predicate.
# Each listener is stored as a tuple: (priority, listener, predicate)
_listener_registry: Dict[str, List[Tuple[int, Callable[[Event], Any], Callable[[Event], bool]]]] = {}
_wildcard_registry: List[Tuple[str, int, Callable[[Event], Any], Callable[[Event], bool]]] = []


def register_listener(event_pattern: str, listener: Callable[[Event], Any], priority: int = 10,
                      predicate: Callable[[Event], bool] = lambda e: True):
    """
    Subscribe a listener to an event pattern with optional predicate filtering.
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
    Retrieve all listeners for an event, including exact and wildcard matches.
    Applies predicate filtering and returns listeners sorted by priority.
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
    This function could forward events to Kafka, RabbitMQ, etc.
    """
    logger.info(
        f"Forwarding event {event.name} to external message bus (Correlation ID: {event.metadata.get('correlation_id')})")


def validate_event(event: Event) -> Event:
    """
    Validate an event against the schema.
    """
    validated = EventSchema(name=event.name, payload=event.payload, metadata=event.metadata)
    return event


def dispatch(event: Union[Event, str], payload: Dict[str, Any] = None, mode: str = 'sync'):
    """
    Dispatch an event with support for multiple execution modes and enhancements.

    Steps:
      1. Convert string to Event (if necessary) and validate.
      2. Enforce rate limiting.
      3. Set up context propagation.
      4. Invoke before-dispatch hooks.
      5. Apply middleware.
      6. Persist the event.
      7. Forward event externally.
      8. Dispatch to listeners (with cancellation and error handling).
      9. Invoke after-dispatch hooks.
    """
    # Step 1: Convert/validate
    if isinstance(event, str):
        event_obj = Event(name=event, payload=payload)
    else:
        event_obj = event

    try:
        event_obj = validate_event(event_obj)
    except Exception as e:
        logger.exception(f"Event validation failed: {e}")
        return

    # Step 2: Rate Limiting
    if not global_rate_limiter.allow(event_obj.name):
        logger.warning(f"Rate limit exceeded for event {event_obj.name}. Dispatch aborted.")
        return

    # Step 3: Context Propagation
    token = current_event_context.set(event_obj.metadata)

    # Step 4: Before-dispatch hooks
    for hook in before_dispatch_hooks:
        try:
            hook(event_obj)
        except Exception as e:
            logger.exception(f"Error in before-dispatch hook: {e}")

    # Step 5: Apply middleware
    for fn in middleware:
        event_obj = fn(event_obj)

    # Step 6: Persist event
    persist_event(event_obj)

    # Step 7: External forwarding
    forward_event_to_bus(event_obj)

    # Start metrics collection
    start_time = time.time()

    # Retrieve listeners (with advanced filtering)
    listeners = get_listeners(event_obj)

    try:
        if mode == 'sync':
            for listener in listeners:
                if event_obj.cancelled:
                    logger.debug(f"Event {event_obj.name} cancelled; stopping propagation.")
                    break
                listener(event_obj)
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
        # Lifecycle error hooks
        for error_hook in on_error_hooks:
            try:
                error_hook(event_obj, dispatch_error)
            except Exception as e:
                logger.exception(f"Error in on_error hook: {e}")
        logger.exception(f"Dispatch error for event {event_obj.name}: {dispatch_error}")
    finally:
        # Step 9: After-dispatch hooks with elapsed time metric.
        elapsed = time.time() - start_time
        for hook in after_dispatch_hooks:
            try:
                hook(event_obj, elapsed)
            except Exception as e:
                logger.exception(f"Error in after-dispatch hook: {e}")
        logger.info(f"Dispatched event {event_obj.name} in {elapsed:.4f} seconds.")
        current_event_context.reset(token)


async def async_listener_wrapper(listener: Callable[[Event], Any], event: Event):
    try:
        result = listener(event)
        if asyncio.iscoroutine(result):
            await result
    except Exception as e:
        logger.exception(f"Error in async listener {listener} for event {event.name}: {e}")
