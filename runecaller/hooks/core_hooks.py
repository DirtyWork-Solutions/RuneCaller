from abc import ABC, abstractmethod

class BaseHook(ABC):
    """
    Abstract base class for hooks.
    """
    @abstractmethod
    def execute(self, *args, **kwargs):
        """Implement hook logic here."""
        pass

# Example default hook
class DefaultPreHook(BaseHook):
    def execute(self, *args, **kwargs):
        print("[DefaultPreHook] Pre-hook executed with:", args, kwargs)
        return args, kwargs
