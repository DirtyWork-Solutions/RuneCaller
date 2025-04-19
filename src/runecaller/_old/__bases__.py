from abc import ABC, abstractmethod


class BaseHook(ABC):
    """
    Abstract base class for hooks.
    """
    @abstractmethod
    def execute(self, *args, **kwargs):
        """Implement hook logic here."""
        pass

class BaseService(ABC):
    pass