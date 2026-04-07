import pytest
from pathlib import Path
from app.core.batch_export import BatchExporter

def test_batch_export_cvs_and_jds(mocker, tmp_path):
    exporter = BatchExporter()
    
    # Create fake app folder
    app_folder = tmp_path / "Google" / "SWE"
    app_folder.mkdir(parents=True)
    
    cv_file = app_folder / "Alice_CV.pdf"
    cv_file.write_text("PDF bytes")
    
    jd_file = app_folder / "job_description.txt"
    jd_file.write_text("JD")
    
    target_dir = tmp_path / "Export_Results"
    
    apps = [
        {
            "company_name": "Google",
            "role_name": "SWE",
            "folder_path": str(app_folder)
        }
    ]
    
    stats = exporter.export(apps, str(target_dir), "Software Engineer")
    
    assert stats["exported_cvs"] == 1
    assert stats["exported_jds"] == 1
    assert (target_dir / "Software Engineer cv 1.pdf").exists()
    assert (target_dir / "Software Engineer jd 1.txt").exists()

def test_batch_export_ignores_missing(mocker, tmp_path):
    exporter = BatchExporter()
    apps = [{"company_name": "Apple", "role_name": "Dev", "folder_path": str(tmp_path / "Missing")}]
    stats = exporter.export(apps, str(tmp_path / "Export"))
    assert len(stats["errors"]) == 1
