import pytest
from app.core.sync_mgr import sync_workspace
from app.core.file_ops import create_application_folder

def test_sync_workspace_cycle(mocker, tmp_path):
    # Mock config so FileOps drops into our temp isolated db/folder
    cv = tmp_path / "cv.docx"
    cv.touch()
    cl = tmp_path / "cl.docx"  
    cl.touch()
    
    mocker.patch("app.core.file_ops.load_config", return_value={
        "user_name": "TestUser", "cv_template_path": str(cv), "cover_letter_template_path": str(cl)
    })
    mocker.patch("app.core.file_ops.get_active_root", return_value=str(tmp_path))
    
    # Run an initial sync on an empty root
    add, upd, rm, dup = sync_workspace(str(tmp_path))
    assert add == 0
    
    # Create an app physically
    create_application_folder("Apple", "Dev")
    
    # Sync should find it and add it
    add, upd, rm, dup = sync_workspace(str(tmp_path))
    assert add == 1
    
    # Sync again should have nothing new
    add, upd, rm, dup = sync_workspace(str(tmp_path))
    assert add == 0
    assert upd == 0
