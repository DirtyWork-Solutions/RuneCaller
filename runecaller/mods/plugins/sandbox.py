import subprocess
import logging

logger = logging.getLogger(__name__)

def run_in_sandbox(command: list):
    """
    Execute a command in a sandboxed subprocess.
    This basic implementation uses subprocess to isolate plugin execution.
    """
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        logger.info(f"Sandboxed command executed: {command}\nOutput: {result.stdout}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Sandboxed command failed: {command}\nError: {e.stderr}")
        return None
