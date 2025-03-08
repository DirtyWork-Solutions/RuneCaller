# A basic registry for hooks: {hook_name: [(priority, hook, enabled, dependencies), ...]}
_hook_registry = {}

def register_hook(name: str, hook, priority: int = 10, enabled: bool = True, dependencies: list = None):
    """
    Registers a hook under a given name.
    - `dependencies` is a list of hook names that must run before this hook.
    """
    dependencies = dependencies or []
    _hook_registry.setdefault(name, []).append((priority, hook, enabled, dependencies))
    # Sort hooks by priority.
    _hook_registry[name].sort(key=lambda tup: tup[0])

def unregister_hook(name: str, hook):
    if name in _hook_registry:
        _hook_registry[name] = [entry for entry in _hook_registry[name] if entry[1] != hook]

def get_registered_hooks(name: str):
    return [entry for entry in _hook_registry.get(name, []) if entry[2]]  # Only enabled hooks
