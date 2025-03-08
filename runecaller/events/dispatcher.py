import asyncio
import time
import logging
import heapq
import sqlite3
import hmac
import hashlib
import json
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)

# Event Middleware System
class Middleware:
    def before_dispatch(self, event):
        return event  # Modify or validate event before sending

    def after_dispatch(self, event, responses):
        return responses  # Post-processing after event is sent

# Default Logging Middleware
class LoggingMiddleware(Middleware):
    def before_dispatch(self, event):
        logging.info(f"Dispatching event: {event['signal']} from {event['sender']}")
        return event

    def after_dispatch(self, event, responses):
        logging.info(f"Event {event['signal']} processed. Responses: {responses}")
        return responses

# Security Middleware for Authorization & Signatures
class SecurityMiddleware(Middleware):
    SECRET_KEY = "my_secure_secret"
    ALLOWED_SENDERS = {"system", "admin"}  # Allowed roles

    def before_dispatch(self, event):
        sender = event["sender"]
        if sender not in self.ALLOWED_SENDERS:
            raise PermissionError(f"Unauthorized sender: {sender}")

        if not self.verify_signature(event):
            raise ValueError("Event signature verification failed")

        return event

    def verify_signature(self, event):
        """Verify event signature using HMAC"""
        received_signature = event.get("signature")
        event_data = json.dumps(event["data"], sort_keys=True).encode()
        expected_signature = hmac.new(self.SECRET_KEY.encode(), event_data, hashlib.sha256).hexdigest()
        return hmac.compare_digest(received_signature, expected_signature)

# Priority Queue for Deferred Events
class EventQueue:
    def __init__(self):
        self.queue = []

    def add_event(self, priority, event):
        heapq.heappush(self.queue, (-priority, time.time(), event))  # Higher priority executes first

    def get_next_event(self):
        if self.queue:
            return heapq.heappop(self.queue)[2]  # Return event
        return None

# Event Persistence
class EventStore:
    def __init__(self, db_path="events.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    signal TEXT,
                    sender TEXT,
                    timestamp REAL,
                    data TEXT
                )
            """)

    def save_event(self, event):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO events (signal, sender, timestamp, data) VALUES (?, ?, ?, ?)",
                         (event['signal'], event['sender'], event['timestamp'], str(event['data'])))

# Enhanced Event Dispatcher
class EventDispatcher:
    def __init__(self, middleware=None, async_event_types=None, system_load_threshold=80):
        self.middleware = middleware or []
        self.async_event_types = async_event_types or []
        self.queue = EventQueue()
        self.event_store = EventStore()
        self.subscriptions = defaultdict(list)
        self.system_load_threshold = system_load_threshold  # Mock system load threshold

    def register_middleware(self, middleware):
        self.middleware.append(middleware)

    def subscribe(self, signal, listener):
        self.subscriptions[signal].append(listener)

    def dispatch(self, signal, sender, priority=0, **data):
        event = {
            "signal": signal,
            "sender": sender,
            "timestamp": time.time(),
            "priority": priority,
            "data": data,
            "signature": self.generate_signature(data)
        }

        # Apply middleware (pre-processing)
        for mw in self.middleware:
            event = mw.before_dispatch(event)

        # Check execution strategy
        if self.should_defer(event):
            self.queue.add_event(priority, event)
            logging.info(f"Event {signal} deferred due to system load.")
            return []

        elif signal in self.async_event_types:
            asyncio.create_task(self.handle_async_event(event))
        else:
            return self.handle_sync_event(event)

    def should_defer(self, event):
        # Mock check for system load
        return len(self.queue.queue) > self.system_load_threshold

    async def handle_async_event(self, event):
        responses = []
        for listener in self.subscriptions.get(event['signal'], []):
            responses.append(await listener(event))
        self.event_store.save_event(event)
        for mw in self.middleware:
            mw.after_dispatch(event, responses)
        return responses

    def handle_sync_event(self, event):
        responses = []
        for listener in self.subscriptions.get(event['signal'], []):
            responses.append(listener(event))
        self.event_store.save_event(event)
        for mw in self.middleware:
            mw.after_dispatch(event, responses)
        return responses

    async def process_queued_events(self):
        while self.queue.queue:
            event = self.queue.get_next_event()
            await self.handle_async_event(event)

    def generate_signature(self, data):
        """Generate HMAC signature for an event"""
        return hmac.new(SecurityMiddleware.SECRET_KEY.encode(), json.dumps(data, sort_keys=True).encode(), hashlib.sha256).hexdigest()

# Example Usage
dispatcher = EventDispatcher(middleware=[LoggingMiddleware(), SecurityMiddleware()], async_event_types=["notification"])

def example_listener(event):
    print(f"Received event: {event}")
    return "Processed"


if __name__ == '__main__':
    dispatcher.subscribe("user.signup", example_listener)
    dispatcher.dispatch("user.signup", "system", priority=5, user_id=123)
