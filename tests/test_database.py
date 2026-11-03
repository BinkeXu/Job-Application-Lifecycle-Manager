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
    
    # Test Detailed Analytics & Metrics
    from app.core.database import get_interviews_secured_count
    assert get_interviews_secured_count() >= 2

    detailed = get_detailed_analytics(None, None)
    assert detailed["total_apps"] >= 2
    assert detailed["offers_count"] == 1
    assert detailed["interviewed_count"] == 1
    assert "offer_rate" in detailed
    assert "interview_rate" in detailed
    assert "interview_success_rate" in detailed
    assert detailed["offer_rate"] == 50.0
    assert detailed["interview_rate"] == 100.0
    assert detailed["interview_success_rate"] == 50.0
    assert len(detailed["offer_roles_list"]) == 1
    assert detailed["offer_roles_list"][0][0] == "Netflix"
    assert detailed["offer_roles_list"][0][1] == "Engineer"
    assert len(detailed["by_company"]) >= 2
    assert len(detailed["by_role"]) >= 2

def test_update_application_job_description():
    from app.core.database import update_application_job_description, get_application_by_id
    app_id = add_application("Stripe", "Backend Engineer", "/stripe/1", job_description="Initial JD")
    app = get_application_by_id(app_id)
    assert app["job_description"] == "Initial JD"
    
    update_application_job_description(app_id, "Updated JD with requirements")
    app_updated = get_application_by_id(app_id)
    assert app_updated["job_description"] == "Updated JD with requirements"

def test_skip_llm_and_dict_returns():
    from app.core.database import add_application, get_mapped_role, get_detailed_analytics, get_application_by_id, get_applications, get_interviews, add_interview
    
    # Test skip_llm bypasses any LLM call
    role = get_mapped_role("senior rust ninja", skip_llm=True)
    assert role == "Senior Rust Ninja"
    
    app_id = add_application("Tesla", "Autopilot Engineer", "/t/1")
    
    # Test get_detailed_analytics with skip_llm
    detailed = get_detailed_analytics(skip_llm=True)
    assert "by_role" in detailed
    
    # Test dict returns and .get() support
    apps = get_applications()
    assert len(apps) > 0
    assert isinstance(apps[0], dict)
    assert apps[0].get("company_name") == "Tesla"
    
    app = get_application_by_id(app_id)
    assert isinstance(app, dict)
    assert app.get("company_name") == "Tesla"
    assert app.get("non_existent_key", "default") == "default"
    
    add_interview(app_id, "Test note")
    interviews = get_interviews(app_id)
    assert len(interviews) > 0
    assert isinstance(interviews[0], dict)
    assert interviews[0].get("notes") == "Test note"

def test_database_search_case_insensitivity_and_filters(isolated_db):
    add_application("Toyota Motor", "Data Analyst", "/mock/toyota")
    add_application("Honda", "Senior Data Analyst", "/mock/honda")
    add_application("Toyota Finance", "Financial Analyst", "/mock/toyota_fin")

    # 1. Test case-insensitivity with general search_query
    lower_res = get_applications(search_query="toyota")
    assert len(lower_res) == 2
    upper_res = get_applications(search_query="TOYOTA")
    assert len(upper_res) == 2
    mixed_res = get_applications(search_query="ToYoTa")
    assert len(mixed_res) == 2

    # 2. Test dedicated company filter
    toyota_comp = get_applications(company="toyota")
    assert len(toyota_comp) == 2
    honda_comp = get_applications(company="HONDA")
    assert len(honda_comp) == 1
    assert honda_comp[0]["company_name"] == "Honda"

    # 3. Test dedicated role filter
    data_roles = get_applications(role="data analyst")
    assert len(data_roles) == 2
    
    # 4. Test combined company + role filter
    combined = get_applications(company="toyota", role="data analyst")
    assert len(combined) == 1
    assert combined[0]["company_name"] == "Toyota Motor"

def test_detailed_analytics_zero_division(isolated_db):
    from app.core.database import get_detailed_analytics, get_interviews_secured_count
    res = get_detailed_analytics()
    assert res["total_apps"] == 0
    assert res["interviews_secured"] == 0
    assert res["offers_count"] == 0
    assert res["offer_rate"] == 0.0
    assert res["interview_rate"] == 0.0
    assert res["interview_success_rate"] == 0.0
    assert res["offer_roles_list"] == []
    assert get_interviews_secured_count() == 0
