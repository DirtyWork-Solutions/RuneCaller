from runecaller.mods.extensions.framework import Extension
from runecaller.events.dispatch import dispatch
from runecaller.hooks.hook_register import register_hook
from runecaller.hooks.hook_executor import execute_hooks
from runecaller.service_locator import ServiceLocator
from runecaller.lifecycles import LifecycleManager

from bedrocked.reporting.reported import logger

class MyExtension(Extension):
    def __init__(self):
        super().__init__(name="MyExtension", version="1.0", dependencies=[])

    def register(self):
        # Register self as a component in the lifecycle manager.
        lifecycle_manager = ServiceLocator.get("lifecycle_manager")
        lifecycle_manager.register_component(self)
        super().register()
        logger.success(f"[MyExtension] Registered successfully.")
        # Register a hook that will be triggered on activation.
        register_hook("extension.on_activate", self.on_activate_hook, priority=10)

    def start(self):
        """
        Called by the lifecycle manager when starting up.
        """
        logger.info(f"[MyExtension] Starting up.")

    def shutdown(self):
        """
        Called by the lifecycle manager during system shutdown.
        """
        logger.info(f"[MyExtension] Shutting down.")

    def activate(self):
        super().activate()
        logger.success(f"[MyExtension] Activated successfully.")
        # Execute hooks upon activation; hooks might dispatch further events.
        hook_results = execute_hooks("extension.on_activate", extension_name=self.name, mode="sync")
        print(f"[MyExtension] Hook results: {hook_results}")
        # Dispatch an event notifying that the extension has activated.
        dispatch("extension.activated", {"extension": self.name})

    def deactivate(self):
        super().deactivate()
        logger.success(f"[MyExtension] Deactivated successfully.")

    def on_activate_hook(self, *args, **kwargs):
        ext_name = kwargs.get("extension_name", "unknown")
        logger.debug(f"[MyExtension] on_activate_hook triggered for {ext_name}.")
        # As part of the hook, dispatch another event.
        dispatch("hook.triggered", {"message": "Activation hook executed in MyExtension."})
        return "hook_success"


# For standalone testing:
if __name__ == "__main__":
    # Register the lifecycle manager in the service locator.
    from runecaller.lifecycles import LifecycleManager

    lifecycle_manager = LifecycleManager()
    ServiceLocator.register("lifecycle_manager", lifecycle_manager)

    # Instantiate, register, and activate the extension.
    ext = MyExtension()
    ext.register()
    lifecycle_manager.start()  # This calls ext.start()
    ext.activate()
    ext.deactivate()
    lifecycle_manager.shutdown()
