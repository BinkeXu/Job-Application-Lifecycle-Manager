import pytest
import os
import json
from pathlib import Path
from app.core.config_mgr import (
    get_active_root, set_active_root, load_config, save_config, is_config_complete
)

def test_config_lifecycle(mocker, tmp_path):
    # Mock paths to tmp_path
    global_cfg = tmp_path / "global_config.json"
    mocker.patch("app.core.config_mgr.get_global_config_path", return_value=global_cfg)
    
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    
    # Global config
    assert get_active_root() is None
    set_active_root(workspace_root)
    assert get_active_root() == str(workspace_root)
    
    # Workspace Config
    cfg = load_config()
    assert cfg["user_name"] == ""
    
    cfg["user_name"] = "Alice"
    cfg["cv_template_path"] = "hello.docx"
    cfg["cover_letter_template_path"] = "hi.docx"
    save_config(cfg)
    
    new_cfg = load_config()
    assert new_cfg["user_name"] == "Alice"
    
    assert is_config_complete() is True
