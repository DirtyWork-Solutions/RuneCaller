from runecaller._old.mods.extensions.framework import Extension
from runecaller._old.events import dispatch
from runecaller._old.events import subscribe, unsubscribe


class TestPlugin(Extension):
    def __init__(self):
        # Initialize with a name, version, and an empty dependency list.
        super().__init__(name="TestPlugin", version="1.0", dependencies=[])

    def register(self):
        # You can add custom registration logic here.
        super().register()
        print(f"[TestPlugin] Registered successfully.")
        # Subscribe to a test event from the events system.
        subscribe("plugin.test", self.handle_test_event)

    def activate(self):
        # Custom activation logic; ensure to call the base activate.
        super().activate()
        print(f"[TestPlugin] Activated successfully.")

    def deactivate(self):
        # Custom deactivation logic; ensure to call the base deactivate.
        super().deactivate()
        print(f"[TestPlugin] Deactivated successfully.")
        # Unsubscribe from the test event.
        unsubscribe("plugin.test", self.handle_test_event)

    def execute(self, *args, **kwargs):
        # This is the main functionality of the plugin.
        print(f"[TestPlugin] Executing with args: {args} and kwargs: {kwargs}")
        # Dispatch an event to notify that execution is happening.
        dispatch("plugin.test", {"action": "execute", "args": args, "kwargs": kwargs})

    def on_event(self, event):
        print("Extension handling event with context:", event.context)
        # For example, modify the context for downstream processing
        event.context["handled_by_extension"] = "ExtensionName"

    def handle_test_event(self, other):
        print(other)


# For standalone testing, run the following block.
if __name__ == "__main__":
    plugin = TestPlugin()
    plugin.register()  # Register the plugin and subscribe to events.
    plugin.activate()  # Activate the plugin.
    plugin.execute("demo", key="value")  # Execute plugin logic and dispatch an event.
    plugin.deactivate()  # Deactivate the plugin and unsubscribe from events.
