from runecaller._old.events.dispatch import register_listener, unregister_listener


def subscribe(event_pattern: str, listener, priority: int = 10):
    """Alias to register a listener to an event with an optional priority."""
    register_listener(event_pattern, listener, priority)

def unsubscribe(event_pattern: str, listener):
    """Alias to unregister a listener from an event."""
    unregister_listener(event_pattern, listener)
