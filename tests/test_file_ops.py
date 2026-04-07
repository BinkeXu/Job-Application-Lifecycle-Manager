import pytest
from pathlib import Path
from app.core.file_ops import (
    create_application_folder, write_jalm_id, scan_for_existing_applications, append_interview_note
)

def test_create_and_scan_applications(mocker, tmp_path):
    # Mock config
    cv = tmp_path / "template.docx"
    cv.write_text("dummy cv")
    
    cl = tmp_path / "cl.docx"
    cl.write_text("dummy cover")
    
    mock_config = {
        "user_name": "TestUser",
        "cv_template_path": str(cv),
        "cover_letter_template_path": str(cl)
    }
    mocker.patch("app.core.file_ops.load_config", return_value=mock_config)
    mocker.patch("app.core.file_ops.get_active_root", return_value=str(tmp_path))
    
    # Create App
    folder, time = create_application_folder("Google", "Data Scientist", "Job Desc")
    assert Path(folder).exists()
    assert (Path(folder) / "job_description.txt").exists()
    
    # Write JALM ID
    write_jalm_id(folder, 5)
    
    # Add Interview Note
    append_interview_note(folder, 1, "Passed HR")
    assert (Path(folder) / "interviews.txt").exists()
    
    # Scan Applications
    apps = scan_for_existing_applications(str(tmp_path))
    assert len(apps) == 1
    assert apps[0]["company"] == "Google"
    assert apps[0]["jalm_id"] == 5
    assert apps[0]["has_interviews"] is True
