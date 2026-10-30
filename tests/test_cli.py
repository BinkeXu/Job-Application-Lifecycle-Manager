import os
import json
import pytest
from pathlib import Path
from cli import main, build_parser

@pytest.fixture
def cli_env(tmp_path, mocker):
    """
    Sets up an isolated root directory with templates and database
    to ensure the user's real data is 100% safe during CLI test execution.
    """
    # Create mock template files
    cv = tmp_path / "CV_Template.docx"
    cv.write_text("dummy cv content")
    cl = tmp_path / "CL_Template.docx"
    cl.write_text("dummy cover letter content")

    mock_config = {
        "user_name": "TestUser",
        "cv_template_path": str(cv),
        "cover_letter_template_path": str(cl),
        "additional_cv_templates": {}
    }
    mocker.patch("app.core.config_mgr.load_config", return_value=mock_config)
    mocker.patch("app.core.file_ops.load_config", return_value=mock_config)
    mocker.patch("app.core.config_mgr.get_active_root", return_value=str(tmp_path))
    mocker.patch("app.core.file_ops.get_active_root", return_value=str(tmp_path))
    mocker.patch("app.core.database.get_active_root", return_value=str(tmp_path))
    
    return tmp_path

def test_cli_add_and_get(cli_env, capsys, monkeypatch):
    # 1. Test CLI add with --json
    monkeypatch.setattr("sys.argv", [
        "jalm", "add", 
        "-c", "Anthropic", 
        "-r", "AI Research Engineer", 
        "--jd", "Build safe AI models.", 
        "--json"
    ])
    code = main()
    assert code == 0

    captured = capsys.readouterr()
    res = json.loads(captured.out)
    assert res["status"] == "success"
    assert res["company"] == "Anthropic"
    assert res["role"] == "AI Research Engineer"
    assert os.path.exists(res["folder_path"])
    assert res["jd_path"] is not None
    assert os.path.exists(res["jd_path"])
    app_id = res["id"]

    # 2. Test CLI get with --json
    monkeypatch.setattr("sys.argv", ["jalm", "get", str(app_id), "--json"])
    code = main()
    assert code == 0

    captured = capsys.readouterr()
    app = json.loads(captured.out)
    assert app["id"] == app_id
    assert app["company_name"] == "Anthropic"
    assert app["job_description"] == "Build safe AI models."

def test_cli_add_duplicate_and_index(cli_env, capsys, monkeypatch):
    # First add
    monkeypatch.setattr("sys.argv", ["jalm", "add", "-c", "Google", "-r", "SWE", "--json"])
    assert main() == 0
    capsys.readouterr()

    # Second add without --index should fail
    monkeypatch.setattr("sys.argv", ["jalm", "add", "-c", "Google", "-r", "SWE", "--json"])
    assert main() == 1
    captured = capsys.readouterr()
    res = json.loads(captured.out)
    assert res["status"] == "error"

    # Third add with --index should succeed with indexed title
    monkeypatch.setattr("sys.argv", ["jalm", "add", "-c", "Google", "-r", "SWE", "--index", "--json"])
    assert main() == 0
    captured = capsys.readouterr()
    res = json.loads(captured.out)
    assert res["status"] == "success"
    assert res["role"] == "SWE (2)"

def test_cli_list_and_search(cli_env, capsys, monkeypatch):
    # Add two records
    monkeypatch.setattr("sys.argv", ["jalm", "add", "-c", "Apple", "-r", "iOS Dev", "--json"])
    main()
    monkeypatch.setattr("sys.argv", ["jalm", "add", "-c", "Microsoft", "-r", "Cloud Dev", "--json"])
    main()
    capsys.readouterr()

    # List all
    monkeypatch.setattr("sys.argv", ["jalm", "list", "--json"])
    assert main() == 0
    apps = json.loads(capsys.readouterr().out)
    assert len(apps) == 2

    # Search filter
    monkeypatch.setattr("sys.argv", ["jalm", "list", "-s", "Apple", "--json"])
    assert main() == 0
    apple_apps = json.loads(capsys.readouterr().out)
    assert len(apple_apps) == 1
    assert apple_apps[0]["company_name"] == "Apple"

def test_cli_set_status_and_jd(cli_env, capsys, monkeypatch, tmp_path):
    # Add record
    monkeypatch.setattr("sys.argv", ["jalm", "add", "-c", "Amazon", "-r", "SDE", "--json"])
    main()
    app_id = json.loads(capsys.readouterr().out)["id"]

    # Update status
    monkeypatch.setattr("sys.argv", ["jalm", "set-status", str(app_id), "Interviewed", "--json"])
    assert main() == 0
    res = json.loads(capsys.readouterr().out)
    assert res["status"] == "success"
    assert res["new_status"] == "Interviewed"

    # Update status with invalid value
    monkeypatch.setattr("sys.argv", ["jalm", "set-status", str(app_id), "InvalidStatus", "--json"])
    assert main() == 1
    capsys.readouterr()

    # Update JD via file
    jd_file = tmp_path / "new_jd.txt"
    jd_file.write_text("Updated distributed systems JD.")
    monkeypatch.setattr("sys.argv", ["jalm", "set-jd", str(app_id), "--jd-file", str(jd_file), "--json"])
    assert main() == 0
    capsys.readouterr()

    # Verify updated JD via get
    monkeypatch.setattr("sys.argv", ["jalm", "get", str(app_id), "--json"])
    main()
    app = json.loads(capsys.readouterr().out)
    assert app["job_description"] == "Updated distributed systems JD."

def test_cli_stats(cli_env, capsys, monkeypatch):
    monkeypatch.setattr("sys.argv", ["jalm", "stats", "--json"])
    assert main() == 0
    stats = json.loads(capsys.readouterr().out)
    assert "total_applications" in stats
    assert "active_interviews" in stats
