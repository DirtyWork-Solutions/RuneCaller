"""
This module provides various enhancements for event handling, including lifecycle hooks, rate limiting, persistence,
event scheduling, security, load monitoring, circuit breaking, and logging.

**Classes:**
    - RateLimiter: Implements rate limiting for event handling.
    - LoadMonitor: Monitors the load based on the number of events in a given time window.
    - CircuitBreaker: Implements a circuit breaker pattern to handle faulty events.
    - LoggingConfig: Configures fine-grained logging levels for different events.

**Functions:**
    - register_before_dispatch: Registers a hook to be called before an event is dispatched.
    - register_after_dispatch: Registers a hook to be called after an event is dispatched.
    - register_on_error: Registers a hook to be called when an error occurs during event dispatch.
    - init_persistence_db: Initializes the persistence database for storing events.
    - persist_event: Persists an event to the database.
    - schedule_event: Schedules an event to be dispatched after a delay.
    - requires_role: Decorator to enforce role-based access control for event listeners.
    - event_stream: Yields events from the persistent storage in order.
    - alert_event: Logs a critical alert for an event.

**Global Instances:**
    - global_rate_limiter: A global instance of RateLimiter with default settings.
    - global_load_monitor: A global instance of LoadMonitor with default settings.
    - global_circuit_breaker: A global instance of CircuitBreaker with default settings.
    - global_logging_config: A global instance of LoggingConfig.
"""

import asyncio
import logging
import time
import sqlite3
import os
import json
from collections import deque
from functools import wraps
from typing import Callable, Any, List, Generator
import contextvars

from bedrocked.reporting.reported import logger

# -------------------------------
# Lifecycle Hooks & Callbacks
# -------------------------------
before_dispatch_hooks: List[Callable[['Event'], None]] = []
after_dispatch_hooks: List[Callable[['Event', float], None]] = []
on_error_hooks: List[Callable[['Event', Exception], None]] = []

def register_before_dispatch(fn: Callable[['Event'], None]):
    """Registers a hook to be called before an event is dispatched."""
    before_dispatch_hooks.append(fn)

def register_after_dispatch(fn: Callable[['Event', float], None]):
    """Registers a hook to be called after an event is dispatched."""
    after_dispatch_hooks.append(fn)

def register_on_error(fn: Callable[['Event', Exception], None]):
    """Registers a hook to be called when an error occurs during event dispatch."""
    on_error_hooks.append(fn)

# -------------------------------
# Rate Limiting & Throttling
# -------------------------------
class RateLimiter:
    """Implements rate limiting for event handling."""
    def __init__(self, max_calls: int, period: float):
        self.max_calls = max_calls
        self.period = period
        self.calls = {}

    def allow(self, key: str) -> bool:
        """Checks if an event is allowed based on the rate limit."""
        now = time.time()
        timestamps = self.calls.get(key, [])
        timestamps = [t for t in timestamps if now - t < self.period]
        if len(timestamps) < self.max_calls:
            timestamps.append(now)
            self.calls[key] = timestamps
            return True
        return False

global_rate_limiter = RateLimiter(max_calls=5, period=1.0)

# -------------------------------
# Persistence & Archiving
# -------------------------------
PERSISTENCE_DB = "event_history.db"

def init_persistence_db():
    """Initializes the persistence database for storing events."""
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
    """Persists an event to the database."""
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
    """Schedules an event to be dispatched after a delay."""
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
        from .event import Event
        yield Event(name=name, payload=payload, metadata=metadata)
    conn.close()

# -------------------------------------------------
# Dynamic Load Adaptation
# -------------------------------------------------
class LoadMonitor:
    """Monitors the load based on the number of events in a given time window."""
    def __init__(self, window_seconds=5, max_events=10):
        self.window_seconds = window_seconds
        self.max_events = max_events
        self.events = deque()

    def record_event(self):
        """Records an event occurrence."""
        now = time.time()
        self.events.append(now)
        while self.events and now - self.events[0] > self.window_seconds:
            self.events.popleft()

    def is_high_load(self) -> bool:
        """Checks if the current load is high."""
        return len(self.events) >= self.max_events

global_load_monitor = LoadMonitor(window_seconds=5, max_events=10)

# -------------------------------------------------
# Circuit Breaker for Faulty Events
# -------------------------------------------------
class CircuitBreaker:
    """Implements a circuit breaker pattern to handle faulty events."""
    def __init__(self, failure_threshold=3, recovery_time=10):
        self.failure_threshold = failure_threshold
        self.recovery_time = recovery_time
        self.failures = {}

    def allow_event(self, event_name: str) -> bool:
        """Checks if an event is allowed based on the failure threshold."""
        if event_name not in self.failures:
            return True
        failure_count, last_failure_time = self.failures[event_name]
        if failure_count < self.failure_threshold:
            return True
        if time.time() - last_failure_time > self.recovery_time:
            self.reset(event_name)
            return True
        return False

    def record_failure(self, event_name: str):
        """Records a failure for an event."""
        now = time.time()
        if event_name in self.failures:
            failure_count, _ = self.failures[event_name]
            self.failures[event_name] = (failure_count + 1, now)
        else:
            self.failures[event_name] = (1, now)
        logger.debug(f"CircuitBreaker: Recorded failure for {event_name}: {self.failures[event_name]}")

    def reset(self, event_name: str):
        """Resets the failure count for an event."""
        if event_name in self.failures:
            logger.debug(f"CircuitBreaker: Resetting failures for {event_name}")
            del self.failures[event_name]

global_circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_time=10)

# -------------------------------------------------
# Fine-Grained Logging & Alerting
# -------------------------------------------------
class LoggingConfig:
    """Configures fine-grained logging levels for different events."""
    def __init__(self):
        self.event_levels = {}

    def set_level(self, event_name: str, level):
        """Sets the logging level for an event."""
        self.event_levels[event_name] = level

    def get_level(self, event_name: str):
        """Gets the logging level for an event."""
        return self.event_levels.get(event_name, logging.INFO)

global_logging_config = LoggingConfig()

def alert_event(event_name: str, message: str):
    """
    Logs a critical alert for an event.
    """
    logger.critical(f"ALERT for event '{event_name}': {message}")