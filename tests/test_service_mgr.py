import pytest
import subprocess
from app.core.service_mgr import ServiceManager

def test_service_manager_lifecycle(mocker, tmp_path):
    mocker.patch("subprocess.Popen")
    
    # Needs to pretend the .exe exists
    exe_path = tmp_path / "JALM.Service.exe"
    exe_path.write_text("binary")
    
    mocker.patch("app.core.service_mgr.ServiceManager.get_service_path", return_value=exe_path)
    
    manager = ServiceManager()
    
    # Clean state
    manager._process = None 
    
    manager.start_service()
    assert manager._process is not None
    
    manager.stop_service()
    assert manager._process is None
