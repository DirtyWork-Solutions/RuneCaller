import asyncio
from runecaller._old.events import dispatch, add_middleware, register_listener
from runecaller._old.events import (
    register_before_dispatch,
    register_after_dispatch,
    register_on_error,
    schedule_event,
    requires_role,
    init_persistence_db
)

# Initialize persistent storage.
init_persistence_db()

# Example middleware that adds custom metadata.
def add_custom_metadata(event):
    event.metadata["custom_field"] = "custom_value"
    return event

add_middleware(add_custom_metadata)

# Lifecycle hooks
def before_hook(event):
    print(f"[Before] About to dispatch: {event.name}")

def after_hook(event, elapsed):
    print(f"[After] Dispatched {event.name} in {elapsed:.4f} seconds.")

def error_hook(event, error):
    print(f"[Error] Error while dispatching {event.name}: {error}")

register_before_dispatch(before_hook)
register_after_dispatch(after_hook)
register_on_error(error_hook)

# Listener with role requirement and predicate filtering.
@requires_role("admin")
def admin_listener(event):
    print(f"Admin listener received: {event}")

def predicate_filter(event):
    # Only process events with payload containing 'process': True.
    return event.payload.get("process", False)

def filtered_listener(event):
    print(f"Filtered listener processed event: {event.name}")

# Register listeners.
register_listener("app.start", admin_listener, priority=5)
register_listener("app.start", filtered_listener, priority=10, predicate=predicate_filter)

# Schedule an event to be dispatched after a 2-second delay.
async def main():
    print("Scheduling event 'app.start' with delayed dispatch...")
    await schedule_event(dispatch, 2, "app.start", {"user": "Alice", "process": True}, mode="sync")
    # Dispatch another event immediately.
    dispatch("app.start", {"user": "Bob", "process": False}, mode="sync")


from runecaller._old.hooks import HookManager
from runecaller._old.hooks import execute_hooks

# Assume we have a configuration file (hooks.yaml) with hook definitions.
# For this demo, we use a sample dictionary.
sample_config = {
    "app.pre_process": [
        {
            "module": "runecaller.hooks.core_hooks",
            "class": "DefaultPreHook",
            "priority": 5,
            "enabled": True,
            "dependencies": []
        }
    ]
}

manager = HookManager()
manager.load_hooks_from_config(sample_config)

# Now, execute hooks for "app.pre_process"
results = execute_hooks("app.pre_process", "sample_arg", key="sample_value")
print("Hook results:", results)



if __name__ == '__main__':
    # Run the example.
    asyncio.run(main())
