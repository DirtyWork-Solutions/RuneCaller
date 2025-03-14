from typing import Dict
from runecaller._old.mods.extensions.policy import PolicyEngine
from runecaller._old.mods.extensions.dependency import DependencyResolver
from runecaller._old.mods.extensions.auditing import audit_event
from bedrocked.reporting.reported import logger

# A registry for loaded plugins
_loaded_plugins: Dict[str, object] = {}

# Initialize policy engine and dependency resolver (singletons for simplicity)
policy_engine = PolicyEngine()
dependency_resolver = DependencyResolver()

def register_plugin(plugin_name: str, plugin_module: object):
    """
    Register a plugin module after enforcing policies and adding to the dependency graph.
    """
    # Enforce policies
    if not policy_engine.enforce_policies(plugin_module):
        print(f"Plugin {plugin_name} did not meet the required policies.")
        return

    _loaded_plugins[plugin_name] = plugin_module
    # Add to dependency graph if it has necessary attributes.
    if hasattr(plugin_module, 'name') and hasattr(plugin_module, 'dependencies'):
        dependency_resolver.add_extension(plugin_module)
    audit_event(plugin_name, "register", {"status": "success"})
    logger.success(f"Plugin {plugin_name} registered.")

def enable_plugin(plugin_name: str):
    plugin = _loaded_plugins.get(plugin_name)
    if plugin and hasattr(plugin, 'activate'):
        plugin.activate()
        audit_event(plugin_name, "activate", {"status": "enabled"})
        logger.success(f"Plugin {plugin_name} enabled.")

def disable_plugin(plugin_name: str):
    plugin = _loaded_plugins.get(plugin_name)
    if plugin and hasattr(plugin, 'deactivate'):
        plugin.deactivate()
        audit_event(plugin_name, "deactivate", {"status": "disabled"})
        logger.success(f"Plugin {plugin_name} disabled.")

def get_plugin(plugin_name: str):
    return _loaded_plugins.get(plugin_name)
