import json
import os
from pathlib import Path

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "root_directory": "",
    "cv_template_path": "",
    "cl_template_path": ""
}

def get_config_path():
    """Returns the absolute path to the config file."""
    # Place config next to the app entry point or in user home?
    # For now, let's keep it in the project root.
    return Path(CONFIG_FILE).absolute()

def load_config():
    """Loads config from json file. Returns default if file doesn't exist."""
    path = get_config_path()
    if not path.exists():
        return DEFAULT_CONFIG
    
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return DEFAULT_CONFIG

def save_config(config_data):
    """Saves config data to config.json."""
    path = get_config_path()
    with open(path, "w") as f:
        json.dump(config_data, f, indent=4)

def is_config_complete():
    """Checks if all required config values are set."""
    config = load_config()
    return all(config.values())
