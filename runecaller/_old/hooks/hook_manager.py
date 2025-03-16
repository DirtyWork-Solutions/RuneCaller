import asyncio
import time
from typing import Callable, Dict, Any, List, Optional

from runecaller._old.__bases__ import BaseHook

from bedrocked.reporting.reported import logger

class Hook(BaseHook):
    def __init__(
        self,
        callback: Callable,
        condition: Callable[[Dict[str, Any]], bool] = lambda ctx: True,
        priority: int = 0,
        name: str = "",
        dependencies: Optional[List[str]] = None
    ):
        self.callback = callback
        self.condition = condition
        self.priority = priority
        self.name = name
        self.dependencies = dependencies or []

class HookManager:
    """
    Advanced management for hooks with asynchronous support, chaining of data flow,
    monitoring and analytics, and a minimal internal event bus.
    """

    def __init__(self):
        # Registry: hook point -> list of Hook objects.
        self.hooks: Dict[str, List[Hook]] = {}
        # Metrics for monitoring: hook point -> list of execution times.
        self.metrics: Dict[str, List[float]] = {}
        # Minimal internal event subscriptions: event name -> async callback.
        self._event_subscriptions: Dict[str, Callable[[str, Dict[str, Any]], Any]] = {}
        # Initialize event subscriptions for already-registered hook points.
        self.subscribe_to_events()

    def subscribe_to_events(self):
        """
        Subscribes the hook manager to events using a minimal internal event bus.
        Each hook point in the registry gets mapped to the trigger_hooks_async method.
        """
        for hook_point in self.hooks.keys():
            self._event_subscriptions[hook_point] = self.trigger_hooks_async
        logger.info("HookManager subscribed to events using the internal event bus.")

    def publish_event(self, hook_point: str, context: Dict[str, Any] = {}):
        """
        Publishes an event by hook point. If a subscription exists for the hook point,
        the corresponding hooks are triggered asynchronously.
        """
        if hook_point in self._event_subscriptions:
            # Run the async trigger using asyncio.
            asyncio.run(self._event_subscriptions[hook_point](hook_point, context))
        else:
            logger.warning(f"No event subscription found for hook point '{hook_point}'.")

    def load_hooks_from_config(self, config: dict):
        """
        Load hook definitions from a configuration dictionary.

        **Expected format:**

        {
          "hook_point": [
              {
                  "module": "path.to.module",
                  "class": "HookClass",
                  "priority": 10,
                  "enabled": True,
                  "dependencies": []
              },
              ...
          ],
          ...
        }
        """
        for hook_point, hook_defs in config.items():
            for hook_def in hook_defs:
                module_path = hook_def.get("module")
                class_name = hook_def.get("class")
                priority = hook_def.get("priority", 10)
                enabled = hook_def.get("enabled", True)
                dependencies = hook_def.get("dependencies", [])
                if not enabled:
                    logger.info(f"Skipping disabled hook '{class_name}' for '{hook_point}'.")
                    continue
                try:
                    module = __import__(module_path, fromlist=[class_name])
                    hook_class = getattr(module, class_name)
                    hook_instance = hook_class()  # Assuming no-arg constructor.
                    self.register_hook(
                        hook_point,
                        hook_instance.execute,
                        condition=lambda ctx: True,  # Default condition; can be extended.
                        priority=priority,
                        name=class_name,
                        dependencies=dependencies
                    )
                    logger.info(f"Registered hook '{class_name}' under '{hook_point}' from config with priority {priority}.")
                except Exception as e:
                    logger.error(f"Error loading hook '{class_name}' from '{module_path}': {e}")

    def register_hook(
        self,
        hook_point: str,
        callback: Callable,
        condition: Callable[[Dict[str, Any]], bool] = lambda ctx: True,
        priority: int = 0,
        name: str = "",
        dependencies: Optional[List[str]] = None
    ):
        """Dynamically registers a hook for a specific hook point."""
        hook = Hook(callback, condition, priority, name, dependencies)
        if hook_point not in self.hooks:
            self.hooks[hook_point] = []
        self.hooks[hook_point].append(hook)
        # Reorder hooks based on dependencies and priority.
        self.hooks[hook_point] = self._resolve_order(self.hooks[hook_point])
        # Ensure the event subscription for this hook point exists.
        if hook_point not in self._event_subscriptions:
            self._event_subscriptions[hook_point] = self.trigger_hooks_async
        logger.info(f"Registered hook '{name}' on '{hook_point}' with priority {priority}.")

    def unregister_hook(self, hook_point: str, name: str):
        """Unregisters a hook by its name from a given hook point."""
        if hook_point in self.hooks:
            before = len(self.hooks[hook_point])
            self.hooks[hook_point] = [hook for hook in self.hooks[hook_point] if hook.name != name]
            after = len(self.hooks[hook_point])
            logger.info(f"Unregistered hook '{name}' from '{hook_point}'. Removed {before - after} hook(s).")

    async def trigger_hooks_async(self, hook_point: str, context: Dict[str, Any] = {}) -> Dict[str, Any]:
        """
        Asynchronously triggers all hooks registered to a hook point.
        Supports chaining: each hook may update the context.
        Records execution metrics for monitoring purposes.
        """
        hooks = self.hooks.get(hook_point, [])
        if not hooks:
            logger.info("No hooks registered for '%s'", hook_point)
            return context

        # Initialize metrics storage for this hook point.
        if hook_point not in self.metrics:
            self.metrics[hook_point] = []

        # Process each hook in order.
        for hook in hooks:
            if not hook.condition(context):
                logger.info("Skipping hook '%s' on '%s'; condition not met.", hook.name, hook_point)
                continue

            start_time = time.perf_counter()
            try:
                # Check if the callback is asynchronous.
                if asyncio.iscoroutinefunction(hook.callback):
                    result = await hook.callback(context)
                else:
                    result = hook.callback(context)
                    if asyncio.isfuture(result) or hasattr(result, '__await__'):
                        result = await result
                end_time = time.perf_counter()

                exec_time = end_time - start_time
                self.metrics[hook_point].append(exec_time)
                logger.info("Executed hook '%s' on '%s' in %.4f seconds.", hook.name, hook_point, exec_time)

                # Chaining: if a hook returns an updated context, merge it.
                if result is not None:
                    if isinstance(result, dict):
                        context.update(result)
                    else:
                        logger.warning("Hook '%s' returned a non-dict value; skipping context merge.", hook.name)
            except Exception as e:
                logger.error("Error executing hook '%s' on '%s': %s", hook.name, hook_point, e)
        return context

    def trigger_hooks(self, hook_point: str, context: Dict[str, Any] = {}) -> Dict[str, Any]:
        """
        Synchronous wrapper to trigger hooks by running the async trigger in an event loop.
        """
        return asyncio.run(self.trigger_hooks_async(hook_point, context))

    def _resolve_order(self, hooks: List[Hook]) -> List[Hook]:
        """
        Orders hooks based on dependencies (if provided) and priority.
        Attempts a topological sort; falls back to simple priority sorting if a cycle is detected.
        """
        # Map named hooks for dependency resolution.
        hook_map = {hook.name: hook for hook in hooks if hook.name}
        in_degree = {name: 0 for name in hook_map}
        graph = {name: [] for name in hook_map}

        # Build the dependency graph.
        for hook in hooks:
            if hook.name:
                for dep in hook.dependencies:
                    if dep in hook_map:
                        graph[dep].append(hook.name)
                        in_degree[hook.name] += 1

        zero_in_degree = [name for name, deg in in_degree.items() if deg == 0]
        zero_in_degree.sort(key=lambda name: hook_map[name].priority, reverse=True)
        sorted_names = []
        while zero_in_degree:
            current = zero_in_degree.pop(0)
            sorted_names.append(current)
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    zero_in_degree.append(neighbor)
                    zero_in_degree.sort(key=lambda name: hook_map[name].priority, reverse=True)

        if len(sorted_names) != len(hook_map):
            logger.warning("Cycle detected in hook dependencies; falling back to priority ordering.")
            return sorted(hooks, key=lambda h: h.priority, reverse=True)

        ordered_hooks = [hook_map[name] for name in sorted_names]
        # Append hooks without a name (or dependencies), sorted by priority.
        unnamed_hooks = [hook for hook in hooks if not hook.name]
        unnamed_hooks.sort(key=lambda h: h.priority, reverse=True)
        return ordered_hooks + unnamed_hooks

    def get_metrics(self, hook_point: str) -> List[float]:
        """Returns the recorded execution times for hooks under a given hook point."""
        return self.metrics.get(hook_point, [])
