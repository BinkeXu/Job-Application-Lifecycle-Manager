import json
import os
import sys
from pathlib import Path

GLOBAL_CONFIG_FILE = "config.json"
WORKSPACE_CONFIG_NAME = "jalm_config.json"

DEFAULT_CONFIG = {
    "user_name": "",
    "cv_template_path": "",
    "cover_letter_template_path": "",
    "additional_cv_templates": {},  # Dictionary mapping template names to their absolute paths
    "ollama_model": "llama3.2"
}

def get_global_config_path():
    if hasattr(sys, '_MEIPASS'):
        # Bundled (PyInstaller): Place config next to the .exe
        return Path(sys.executable).parent / GLOBAL_CONFIG_FILE
    else:
        # Dev mode: Place config in the project root
        return Path(__file__).parent.parent.parent / GLOBAL_CONFIG_FILE

def get_active_root():
    """Returns the current active root directory from global config."""
    global_path = get_global_config_path()
    if not global_path.exists():
        return None
    try:
        with open(global_path, "r") as f:
            data = json.load(f)
            # Migration check: handle old config format
            if "root_directory" in data and "active_root" not in data:
                active_root = data["root_directory"]
                set_active_root(active_root)
                return active_root
            return data.get("active_root")
    except Exception as e:
        print(f"Error reading global config (get_active_root): {e}")
        return None

def set_active_root(root_path):
    """Sets the active root directory in global config (preserves other keys)."""
    global_path = get_global_config_path()
    data = {}
    if global_path.exists():
        try:
            with open(global_path, "r") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error reading global config (set_active_root): {e}")
    data["active_root"] = str(root_path)
    with open(global_path, "w") as f:
        json.dump(data, f, indent=4)

def get_workspace_config_path():
    """Returns path to the config file inside the active root."""
    root = get_active_root()
    if not root:
        return None
    return Path(root) / WORKSPACE_CONFIG_NAME

def load_config():
    """Loads workspace config. Returns default if not found."""
    path = get_workspace_config_path()
    if not path or not path.exists():
        return DEFAULT_CONFIG
    
    try:
        with open(path, "r") as f:
            data = json.load(f)
            # Migration: check for old "cl_template_path"
            if "cl_template_path" in data and "cover_letter_template_path" not in data:
                data["cover_letter_template_path"] = data["cl_template_path"]
            return data
    except Exception as e:
        print(f"Error loading workspace config: {e}")
        return DEFAULT_CONFIG

def save_config(config_data):
    """Saves config to the workspace-specific file."""
    path = get_workspace_config_path()
    if not path:
        return
    
    # Ensure root exists
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, "w") as f:
        json.dump(config_data, f, indent=4)

def is_config_complete():
    """Checks if root is set AND workspace config is complete."""
    root = get_active_root()
    if not root:
        return False
    
    config = load_config()
    # Check if templates and user name are set
    return (config.get("user_name") != "" and 
            config.get("cv_template_path") != "" and 
            config.get("cover_letter_template_path") != "")
