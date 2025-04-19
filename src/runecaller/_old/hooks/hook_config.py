import json
import os
import yaml

def load_hook_config(file_path: str) -> dict:
    """
    Load hook configuration from a JSON or YAML file.
    """
    _, ext = os.path.splitext(file_path)
    with open(file_path, "r") as f:
        if ext.lower() in [".yaml", ".yml"]:
            return yaml.safe_load(f)
        elif ext.lower() == ".json":
            return json.load(f)
        else:
            raise ValueError("Unsupported configuration file format.")
