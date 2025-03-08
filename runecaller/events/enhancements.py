import asyncio
import time
import logging
import sqlite3
import os
import json
from functools import wraps
from typing import Callable, Any, List, Generator
import contextvars

logger = logging.getLogger(__name__)

# -------------------------------
# Lifecycle Hooks & Callbacks
# -------------------------------
before_dispatch_hooks: List[Callable[['Event'], None]] = []
after_dispatch_hooks: List[Callable[['Event', float], None]] = []
on_error_hooks: List[Callable[['Event', Exception], None]] = []


def register_before_dispatch(fn: Callable[['Event'], None]):
    before_dispatch_hooks.append(fn)


def register_after_dispatch(fn: Callable[['Event', float], None]):
    after_dispatch_hooks.append(fn)


def register_on_error(fn: Callable[['Event', Exception], None]):
    on_error_hooks.append(fn)


# -------------------------------
# Rate Limiting & Throttling
# -------------------------------
class RateLimiter:
    def __init__(self, max_calls: int, period: float):
        self.max_calls = max_calls
        self.period = period
        self.calls = {}

    def allow(self, key: str) -> bool:
        now = time.time()
        timestamps = self.calls.get(key, [])
        # Remove timestamps older than the period
        timestamps = [t for t in timestamps if now - t < self.period]
        if len(timestamps) < self.max_calls:
            timestamps.append(now)
            self.calls[key] = timestamps
            return True
        return False


# Global rate limiter instance (default: 5 calls per second per event type)
global_rate_limiter = RateLimiter(max_calls=5, period=1.0)

# -------------------------------
# Persistence & Archiving
# -------------------------------
PERSISTENCE_DB = "event_history.db"


def init_persistence_db():
    if not os.path.exists(PERSISTENCE_DB):
        conn = sqlite3.connect(PERSISTENCE_DB)
        c = conn.cursor()
        c.execute("""
        CREATE TABLE events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            payload TEXT,
            metadata TEXT,
            timestamp TEXT
        )
        """)
        conn.commit()
        conn.close()


def persist_event(event: 'Event'):
    try:
        conn = sqlite3.connect(PERSISTENCE_DB)
        c = conn.cursor()
        c.execute("INSERT INTO events (name, payload, metadata, timestamp) VALUES (?, ?, ?, ?)",
                  (event.name, json.dumps(event.payload), json.dumps(event.metadata), event.metadata.get("timestamp")))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.exception(f"Failed to persist event: {e}")


# -------------------------------
# Event Scheduling & Deferred Processing
# -------------------------------
async def schedule_event(dispatch_fn: Callable, delay: float, *args, **kwargs):
    await asyncio.sleep(delay)
    dispatch_fn(*args, **kwargs)


# -------------------------------
# Security & Access Control
# -------------------------------
def requires_role(required_role: str):
    """
    Decorator for listeners to require a specific role in the event metadata.
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(event, *args, **kwargs):
            role = event.metadata.get("role")
            if role != required_role:
                logger.warning(f"Access denied for event {event.name}: required role '{required_role}', found '{role}'")
                return
            return fn(event, *args, **kwargs)

        return wrapper

    return decorator


# -------------------------------
# Reactive Programming & Stream Processing
# -------------------------------
def event_stream() -> Generator['Event', None, None]:
    """
    Yields events from the persistent storage in order.
    """
    conn = sqlite3.connect(PERSISTENCE_DB)
    c = conn.cursor()
    for row in c.execute("SELECT name, payload, metadata, timestamp FROM events ORDER BY id ASC"):
        name, payload_str, metadata_str, timestamp = row
        try:
            payload = json.loads(payload_str)
            metadata = json.loads(metadata_str)
        except Exception:
            payload, metadata = {}, {}
        # Create an Event instance (import locally to avoid circular dependency)
        from .event import Event
        yield Event(name=name, payload=payload, metadata=metadata)
    conn.close()


import time
import logging
from collections import deque

logger = logging.getLogger(__name__)


# -------------------------------------------------
# Dynamic Load Adaptation
# -------------------------------------------------
class LoadMonitor:
    def __init__(self, window_seconds=5, max_events=10):
        self.window_seconds = window_seconds
        self.max_events = max_events
        self.events = deque()  # Stores timestamps of recent events

    def record_event(self):
        now = time.time()
        self.events.append(now)
        # Remove events older than the window period
        while self.events and now - self.events[0] > self.window_seconds:
            self.events.popleft()

    def is_high_load(self) -> bool:
        return len(self.events) >= self.max_events


# Global load monitor instance (configurable)
global_load_monitor = LoadMonitor(window_seconds=5, max_events=10)


# -------------------------------------------------
# Circuit Breaker for Faulty Events
# -------------------------------------------------
class CircuitBreaker:
    def __init__(self, failure_threshold=3, recovery_time=10):
        self.failure_threshold = failure_threshold
        self.recovery_time = recovery_time  # in seconds
        self.failures = {}  # event_name -> (failure_count, last_failure_time)

    def allow_event(self, event_name: str) -> bool:
        if event_name not in self.failures:
            return True
        failure_count, last_failure_time = self.failures[event_name]
        if failure_count < self.failure_threshold:
            return True
        # Check if recovery time has passed
        if time.time() - last_failure_time > self.recovery_time:
            self.reset(event_name)
            return True
        return False

    def record_failure(self, event_name: str):
        now = time.time()
        if event_name in self.failures:
            failure_count, _ = self.failures[event_name]
            self.failures[event_name] = (failure_count + 1, now)
        else:
            self.failures[event_name] = (1, now)
        logger.debug(f"CircuitBreaker: Recorded failure for {event_name}: {self.failures[event_name]}")

    def reset(self, event_name: str):
        if event_name in self.failures:
            logger.debug(f"CircuitBreaker: Resetting failures for {event_name}")
            del self.failures[event_name]


# Global circuit breaker instance
global_circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_time=10)


# -------------------------------------------------
# Fine-Grained Logging & Alerting
# -------------------------------------------------
class LoggingConfig:
    def __init__(self):
        self.event_levels = {}  # event_name -> logging level

    def set_level(self, event_name: str, level):
        self.event_levels[event_name] = level

    def get_level(self, event_name: str):
        return self.event_levels.get(event_name, logging.INFO)


# Global logging configuration instance
global_logging_config = LoggingConfig()


def alert_event(event_name: str, message: str):
    """
    Stub for an alerting mechanism.
    For now, this function logs a critical alert.
    It can be extended to send notifications (email, SMS, etc.).
    """
    logger.critical(f"ALERT for event '{event_name}': {message}")
