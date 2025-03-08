import logging
from runecaller.hooks.hook_register import register_hook, get_registered_hooks

logger = logging.getLogger(__name__)


class HookManager:
    """
    Advanced management for hooks, including enabling/disabling,
    ordering based on dependencies, and dynamic reloading.
    """

    def __init__(self):
        self.registry = {}

    def load_hooks_from_config(self, config: dict):
        """
        Load hook definitions from a configuration dictionary.
        Expected format:
        {
          "hook_name": [
              {"module": "path.to.module", "class": "HookClass", "priority": 10, "enabled": True, "dependencies": []},
              ...
          ],
          ...
        }
        """
        # Pseudocode: dynamically import modules and register hooks.
        for hook_name, hook_defs in config.items():
            for hook_def in hook_defs:
                module_path = hook_def["module"]
                class_name = hook_def["class"]
                priority = hook_def.get("priority", 10)
                enabled = hook_def.get("enabled", True)
                dependencies = hook_def.get("dependencies", [])
                # Dynamic import (omitting error handling for brevity)
                module = __import__(module_path, fromlist=[class_name])
                hook_class = getattr(module, class_name)
                hook_instance = hook_class()
                register_hook(hook_name, hook_instance, priority, enabled, dependencies)
                logger.info(f"Registered hook '{class_name}' under '{hook_name}' from config.")

    def enable_hook(self, hook_name: str, hook_instance):
        # Logic to enable a hook.
        # (You may need to update the registry to mark the hook as enabled.)
        pass

    def disable_hook(self, hook_name: str, hook_instance):
        # Logic to disable a hook.
        pass

    def get_ordered_hooks(self, hook_name: str):
        """
        Return hooks ordered by priority and dependencies.
        """
        hooks = get_registered_hooks(hook_name)
        # If dependencies need to be resolved, do so here.
        # For now, we return by priority.
        return sorted(hooks, key=lambda entry: entry[0])
