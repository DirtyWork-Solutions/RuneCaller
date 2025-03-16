# MiddlewareManager class to manage middleware for events
from typing import Callable, Any, Dict, Tuple, List

class MiddlewareManager:
    def __init__(self):
        self._middleware: List[Callable] = []

    def add_middleware(self, middleware: Callable):
        """Add middleware to the manager."""
        self._middleware.append(middleware)

    def remove_middleware(self, middleware: Callable):
        """Remove middleware from the manager."""
        self._middleware.remove(middleware)

    def clear_middleware(self):
        """Clear all middleware from the manager."""
        self._middleware.clear()

    def process(self, signal: Any, sender: Any, **kwargs) -> Tuple[Any, Any, Dict]:
        """Process an event through all middleware."""
        for middleware in self._middleware:
            signal, sender, kwargs = middleware(signal, sender, **kwargs)
        return signal, sender, kwargs