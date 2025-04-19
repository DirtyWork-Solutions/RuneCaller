# EventFilter class to define and apply filters to events
from typing import Callable, Any, Dict, List

class EventFilter:
    def __init__(self, condition: Callable[[Any, Any, Dict], bool]):
        self._condition = condition

    def apply(self, signal: Any, sender: Any, **kwargs) -> bool:
        """Apply the filter to an event."""
        return self._condition(signal, sender, **kwargs)

class EventFilterManager:
    def __init__(self):
        self._filters: List[EventFilter] = []

    def add_filter(self, event_filter: EventFilter):
        """Add a filter to the manager."""
        self._filters.append(event_filter)

    def remove_filter(self, event_filter: EventFilter):
        """Remove a filter from the manager."""
        self._filters.remove(event_filter)

    def apply_filters(self, signal: Any, sender: Any, **kwargs) -> bool:
        """Apply all filters to an event."""
        return all(event_filter.apply(signal, sender, **kwargs) for event_filter in self._filters)