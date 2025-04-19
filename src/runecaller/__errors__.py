"""
TODO: Document module
"""

from pyforged.__errors__ import PyForgedException


#
_NATIVE_ALLOCATIONS = {
    "namespaces": [],
    "something": None
}


# (Non-abstract) base of all pyforged ecosystem exceptions
class RuneCallerException(PyForgedException):  # TODO: Register centrally??
    pass


#
class EventsException(RuneCallerException):
    pass


#
class HooksException(RuneCallerException):
    """

    """
    pass


#
class ModsException(RuneCallerException):
    """

    """
    pass


#
class BackendException(RuneCallerException):
    """

    """
    pass


class ErrorHandler:  # TODO: Actually create the handler
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ErrorHandler, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self.errors = []

    def log_error(self, error):
        self.errors.append(error)

    def get_errors(self):
        return self.errors

    def clear_errors(self):
        self.errors.clear()