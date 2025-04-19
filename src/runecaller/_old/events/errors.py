"""Error types for dispatcher mechanism
"""

class DispatcherError(Exception):
    """Base class for all dispatcher-related errors."""
    pass

class DispatcherKeyError(DispatcherError, KeyError):
    """Raised when a key is not found in the dispatcher."""
    pass

class DispatcherTypeError(DispatcherError, TypeError):
    """Raised when a type error occurs in the dispatcher."""
    pass

class DispatcherValueError(DispatcherError, ValueError):
    """Raised when a value error occurs in the dispatcher."""
    pass
