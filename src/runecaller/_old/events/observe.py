from bedrocked.reporting.reported import logger


def log_event(event):
    """Observer that logs event details, including cancellation status."""
    logger.info(f"Event observed: {event.name}, payload: {event.payload}, metadata: {event.metadata}, cancelled: {event.cancelled}")

def debug_event(event):
    """Detailed debug logging for events."""
    logger.debug(f"Event debug: {event}")

