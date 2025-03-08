import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def audit_event(extension_name: str, event_type: str, details: dict):
    """
    Record an audit log entry for extension events (activation, deactivation, reloading, etc.).
    """
    timestamp = datetime.utcnow().isoformat()
    log_entry = {
        'extension': extension_name,
        'event': event_type,
        'timestamp': timestamp,
        'details': details
    }
    logger.info(f"Audit log: {log_entry}")
    # Optionally, write this log entry to an external auditing system or file.
