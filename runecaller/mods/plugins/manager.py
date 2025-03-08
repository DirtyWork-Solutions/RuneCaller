from typing import Dict

# A registry for loaded plugins
_loaded_plugins: Dict[str, object] = {}

def register_plugin(plugin_name: str, plugin_module: object):
    """Register a plugin module."""
    _loaded_plugins[plugin_name] = plugin_module
    print(f"Plugin {plugin_name} registered.")

def enable_plugin(plugin_name: str):
    """Enable a registered plugin."""
    plugin = _loaded_plugins.get(plugin_name)
    if plugin and hasattr(plugin, 'activate'):
        plugin.activate()
        print(f"Plugin {plugin_name} enabled.")

def disable_plugin(plugin_name: str):
    """Disable a registered plugin."""
    plugin = _loaded_plugins.get(plugin_name)
    if plugin and hasattr(plugin, 'deactivate'):
        plugin.deactivate()
        print(f"Plugin {plugin_name} disabled.")

def get_plugin(plugin_name: str):
    """Retrieve a registered plugin."""
    return _loaded_plugins.get(plugin_name)
