import asyncio
import time
from bedrocked.reporting.reported import logger


# Global middleware for hooks
_hook_middleware = []


def add_hook_middleware(fn):
    """Register a middleware function for hooks."""
    _hook_middleware.append(fn)


def apply_middleware(name: str, args, kwargs):
    for mw in _hook_middleware:
        args, kwargs = mw(name, args, kwargs)
    return args, kwargs


def execute_hooks(name: str, *args, mode: str = 'sync', **kwargs):
    """
    Executes all hooks for a given name with support for:
      - Middleware application
      - Lifecycle callbacks
      - Execution modes: sync, async, deferred
    """
    from runecaller.hooks.hook_register import get_registered_hooks
    hooks = get_registered_hooks(name)

    # Apply middleware to the arguments
    args, kwargs = apply_middleware(name, args, kwargs)

    results = []
    start_time = time.time()

    if mode == 'sync':
        for priority, hook, enabled, deps in hooks:
            try:
                result = hook.execute(*args, **kwargs)
                results.append(result)
            except Exception as e:
                logger.exception(f"Error executing hook {hook} for '{name}': {e}")
    elif mode == 'async':
        loop = asyncio.get_event_loop()
        tasks = []
        for priority, hook, enabled, deps in hooks:
            tasks.append(loop.create_task(async_hook_wrapper(hook, *args, **kwargs)))
        results = tasks  # Caller can await them.
    elif mode == 'deferred':
        logger.debug(f"Deferred execution for hook '{name}' with args {args} and kwargs {kwargs}")
    else:
        raise ValueError("Invalid mode. Use 'sync', 'async', or 'deferred'.")

    elapsed = time.time() - start_time
    logger.info(f"Executed hooks for '{name}' in {elapsed:.4f} seconds.")
    return results


async def async_hook_wrapper(hook, *args, **kwargs):
    try:
        result = hook.execute(*args, **kwargs)
        if asyncio.iscoroutine(result):
            return await result
        return result
    except Exception as e:
        logger.exception(f"Error in async hook {hook}: {e}")


import concurrent.futures

executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)

def execute_hook_isolated(hook, *args, **kwargs):
    return executor.submit(hook.execute, *args, **kwargs)


def audit_hook_execution(hook_name, inputs, outputs, exec_time):
    logger.info(f"Hook {hook_name} executed in {exec_time:.4f}s; inputs: {inputs}, outputs: {outputs}")
