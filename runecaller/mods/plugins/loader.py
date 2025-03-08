import os
import importlib
from typing import List

def discover_plugins(plugin_directory: str) -> List[str]:
    """
    Discover plugin modules within the given directory.
    For now, simply list .py files (excluding __init__.py).
    """
    plugins = []
    for file in os.listdir(plugin_directory):
        if file.endswith('.py') and file != '__init__.py':
            module_name = file[:-3]
            plugins.append(module_name)
    return plugins

def load_plugin(plugin_directory: str, plugin_name: str):
    """
    Dynamically import a plugin module.
    """
    module_path = f"{plugin_directory}.{plugin_name}"
    try:
        module = importlib.import_module(module_path)
        return module
    except ImportError as e:
        print(f"Error loading plugin {plugin_name}: {e}")
        return None
