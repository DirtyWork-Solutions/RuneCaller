from typing import Callable
from bedrocked.reporting.reported import logger
from runecaller._old.__bases__ import BaseHook


# Example default hook
class DefaultPreHook(BaseHook):
    def execute(self, *args, **kwargs):
        logger.debug("[DefaultPreHook] Pre-hook executed with:", args, kwargs)
        return args, kwargs


###
from functools import lru_cache

def cached_hook(fn):
    cached_fn = lru_cache(maxsize=128)(fn)
    def wrapper(*args, **kwargs):
        return cached_fn(*args, **kwargs)
    return wrapper



#####

import time

def retry_hook(fn, retries=3, backoff=0.5):
    def wrapper(*args, **kwargs):
        attempt = 0
        while attempt < retries:
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                attempt += 1
                time.sleep(backoff * (2 ** (attempt - 1)))  # exponential backoff
        raise Exception(f"Hook {fn.__name__} failed after {retries} attempts")
    return wrapper


######
def conditionally_enabled(condition: Callable[[], bool]):
    def decorator(fn):
        fn._enabled_condition = condition
        return fn
    return decorator



