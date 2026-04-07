import pytest
from app.core.database import (
    add_application, 
    get_applications, 
    add_interview, 
    get_interviews,
    delete_application,
    get_mapped_role
)

def test_add_and_get_application():
    app_id = add_application("Google", "Software Engineer", "/mock/path")
    assert app_id > 0
    apps = get_applications()
    assert len(apps) == 1
    assert apps[0]["company_name"] == "Google"
    assert apps[0]["role_name"] == "Software Engineer"
    assert apps[0]["folder_path"] == "/mock/path"

def test_add_interview_creates_sequence():
    app_id = add_application("Apple", "Dev", "/mock/path/2")
    seq1 = add_interview(app_id, "First round with HR")
    seq2 = add_interview(app_id, "Technical round")
    
    assert seq1 == 1
    assert seq2 == 2
    
    interviews = get_interviews(app_id)
    assert len(interviews) == 2
    assert interviews[0]["sequence"] == 1
    assert interviews[0]["notes"] == "First round with HR"

def test_delete_application_cascades_interviews():
    app_id = add_application("Meta", "Engineer", "/mock/path/3")
    add_interview(app_id, "Note")
    
    delete_application(app_id)
    
    apps = get_applications()
    assert len(apps) == 0
    # Interviews should cascade delete in the DB 
    interviews = get_interviews(app_id)
    assert len(interviews) == 0

def test_get_mapped_role_fallback(mocker):
    # Mock LLM classify_job_title to throw an error 
    mocker.patch("app.core.llm_service.classify_job_title", side_effect=Exception("Failed API"))
    
    # Should fallback to title case
    category = get_mapped_role("junior graphic DESIGNER")
    assert category == "Junior Graphic Designer"

def test_analytics_and_status_functions():
    # Insert multiple apps
    from app.core.database import update_application_status, get_analytics_data, get_daily_status_counts, get_detailed_analytics, add_interview, application_exists, count_applications_with_name, remove_duplicates, get_application_by_id
    app1 = add_application("Netflix", "Engineer", "/n/1")
    app2 = add_application("Hulu", "Designer", "/h/1")
    app3 = add_application("Hulu", "Designer", "/h/1") # duplicate folder path
    
    # Add interview to trigger 'interviews secured' count
    add_interview(app2, "Initial HR screening")
    
    # Check basics
    assert application_exists("Netflix", "Engineer")
    assert count_applications_with_name("Hulu", "Designer") == 2
    
    # Remove duplicates
    removed = remove_duplicates()
    assert removed == 1
    
    # Get by ID
    app = get_application_by_id(app1)
    assert app["company_name"] == "Netflix"
    
    # Update statuses
    update_application_status(app1, "Offer")
    update_application_status(app2, "Interviewed")
    
    # Test Analytics Data
    status_counts, latest = get_analytics_data()
    assert status_counts.get("Offer") >= 1
    assert status_counts.get("Interviewed") >= 1
    assert len(latest) >= 1
    
    # Test Daily Status Counts
    daily = get_daily_status_counts(None, None)
    assert len(daily) > 0
    assert daily[0][1] == "Offer" or daily[0][1] == "Interviewed"
    
    # Test Detailed Analytics
    detailed = get_detailed_analytics(None, None)
    assert detailed["total_apps"] >= 2
    assert detailed["offers_count"] == 1
    assert detailed["interviewed_count"] == 1
    assert len(detailed["by_company"]) >= 2
    assert len(detailed["by_role"]) >= 2
