import importlib
import logging

logger = logging.getLogger(__name__)

def reload_extension(extension_module):
    """
    Dynamically reload an extension module.
    This allows updating the extension at runtime without restarting the application.
    """
    try:
        new_module = importlib.reload(extension_module)
        logger.info(f"Extension {extension_module.__name__} reloaded successfully.")
        return new_module
    except Exception as e:
        logger.exception(f"Failed to reload extension {extension_module.__name__}: {e}")
        return None
