from bedrocked.reporting.reported import logger
from pyforged.engine.services import ServiceRegistry

from runecaller.events.event import Event
from runecaller.events.dispatch import dispatch

from pyforged.engine.services import ServiceRegistry


_persistent_services = ServiceRegistry()

class ServiceLocator:
    _services = {}
    _aliases = {}

    @classmethod
    def register(cls, name: str, service: object):
        dispatch(Event("engine.services.registered",
                       context={"name": name,
                                "obj_type": service.__class__.__name__}))
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
            dispatch(Event("engine.services.unregistered",
                           context={"name": name}))
            del cls._services[name]

# Example usage:
# ServiceLocator.register("event_system", my_event_system_instance)
# event_system = ServiceLocator.get("event_system")
if __name__ == '__main__':
    ServiceLocator.register("logs", logger)
    ServiceLocator.register("persistence", _persistent_services)

    logs = ServiceLocator.get("logs")
    logs.success("Boo")