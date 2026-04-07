import pytest
from app.core.llm_service import classify_job_title

def test_classify_job_title_success(mocker):
    # Mock urllib.request.urlopen returning a successful response
    mock_response = mocker.Mock()
    mock_response.read.return_value = b'{"response": "Data Engineer"}'
    
    mock_urlopen = mocker.patch("urllib.request.urlopen")
    mock_urlopen.return_value.__enter__.return_value = mock_response
    
    mocker.patch("app.core.llm_service.get_current_model", return_value="llama3.2")
    mocker.patch("app.core.llm_service.CATEGORIES", ["Software Engineer", "Data Engineer"])
    
    result = classify_job_title("spark scala developer")
    assert result == "Data Engineer"

def test_classify_job_title_invalid_json(mocker):
    # Ensure it falls back to title case on failure
    mock_urlopen = mocker.patch("urllib.request.urlopen", side_effect=Exception("Connection refused"))
    mocker.patch("app.core.llm_service.get_current_model", return_value="llama3.2")
    
    result = classify_job_title("frontend wizard")
    assert result == "Frontend Wizard"
