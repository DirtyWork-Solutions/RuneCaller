from bedrocked.reporting.reported import logger
from pyforged.services import ServiceRegistry

class ServiceLocator:
    _services = {}

    @classmethod
    def register(cls, name: str, service: object):
        cls._services[name] = service

    @classmethod
    def get(cls, name: str) -> object:
        service = cls._services.get(name)
        if service is None:
            raise Exception(f"Service '{name}' not found.")
        return service

    @classmethod
    def unregister(cls, name: str):
        if name in cls._services:
            del cls._services[name]

# Example usage:
# ServiceLocator.register("event_system", my_event_system_instance)
# event_system = ServiceLocator.get("event_system")
if __name__ == '__main__':
    ServiceLocator.register("logs", logger)
    logs = ServiceLocator.get("logs")
    logs.success("Boo")