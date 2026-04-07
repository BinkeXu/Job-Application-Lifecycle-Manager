import pytest
import os
import sqlite3

@pytest.fixture(autouse=True)
def isolated_db(mocker, tmp_path):
    """
    Forces all tests to use an isolated SQLite database in a temporary directory
    instead of the real user's jalm_apps.db.
    """
    mocker.patch("app.core.database.DB_NAME", "test_jalm_apps.db")
    mocker.patch("app.core.database.get_active_root", return_value=str(tmp_path))
    
    # Run the init to create tables in the temp db
    from app.core.database import init_db
    init_db()
    
    yield
    # No teardown needed, tmp_path cleans up automatically
