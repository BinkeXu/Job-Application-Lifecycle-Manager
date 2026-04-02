import sqlite3
import os
from datetime import datetime

from .config_mgr import get_active_root
import threading

DB_NAME = "jalm_apps.db"

# This function creates a "Pipe" to the SQLite database file.
def get_db_connection():
    """Establishes a connection to the SQLite database inside the active root."""
    root = get_active_root()
    if not root:
        # If no project is selected yet, save the DB in the current folder.
        conn = sqlite3.connect(DB_NAME)
    else:
        # Otherwise, save it inside the user's chosen "Root" folder.
        db_path = os.path.join(root, DB_NAME)
        conn = sqlite3.connect(db_path)
        
    conn.row_factory = sqlite3.Row
    
    # ADVANCED: We enable "Write-Ahead Logging" (WAL) mode.
    # This keeps the database fast and allows BOTH the Python UI and the 
    # .NET Background Service to read/write at the same time without crashing.
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=5000") # Wait up to 5 seconds if the file is busy.
    conn.execute("PRAGMA foreign_keys=ON")   # Enable cascade deletes globally.
    
    return conn

# This "Initializes" the database by creating tables if they don't exist.
def init_db():
    """Initializes the database with the required tables."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # 1. table for all your job applications.
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                role_name TEXT NOT NULL,
                folder_path TEXT NOT NULL,
                status TEXT DEFAULT 'Applied',
                job_description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Migration: Add job_description column if it doesn't exist (for existing users)
        cursor.execute("PRAGMA table_info(applications)")
        columns = [row[1] for row in cursor.fetchall()]
        if "job_description" not in columns:
            cursor.execute("ALTER TABLE applications ADD COLUMN job_description TEXT")

        # 2. table for tracking interview notes.
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_id INTEGER NOT NULL,
                sequence INTEGER NOT NULL,
                notes TEXT,
                date DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (app_id) REFERENCES applications (id) ON DELETE CASCADE
            )
        ''')

        # 3. Create "Indexes" to make searching for companies super fast.
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_apps_company ON applications(company_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_apps_role ON applications(role_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_apps_created ON applications(created_at)')

        # Migration: Rename 'Interviewing' to 'Interviewed'
        cursor.execute("UPDATE applications SET status = 'Interviewed' WHERE status = 'Interviewing'")

        # 4. table for caching role categorizations (LLM)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS role_mappings (
                original_role TEXT PRIMARY KEY,
                mapped_category TEXT NOT NULL
            )
        ''')


        conn.commit()
    finally:
        conn.close()

def get_mapped_role(role_name):
    """Checks the database for a cached category, otherwise asks the LLM and caches it."""
    if not role_name:
        return "Unknown Role"
        
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT mapped_category FROM role_mappings WHERE original_role = ?', (role_name,))
        row = cursor.fetchone()
        
        if row:
            return row[0]
            
        # If not found, call LLM
        try:
            from .llm_service import classify_job_title
            category = classify_job_title(role_name)
        except Exception as e:
            print(f"LLM Classification failed for '{role_name}': {e}")
            category = role_name.title() # fallback

        # Cache the result
        try:
            cursor.execute("INSERT OR IGNORE INTO role_mappings (original_role, mapped_category) VALUES (?, ?)", (role_name, category))
            conn.commit()
        except Exception as e:
            print(f"Failed to cache role mapping: {e}")
            
        return category
    finally:
        conn.close()

def add_application(company, role, folder_path, created_at=None, job_description=None):
    """Inserts a new application record."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        if created_at:
            cursor.execute('''
                INSERT INTO applications (company_name, role_name, folder_path, created_at, job_description)
                VALUES (?, ?, ?, ?, ?)
            ''', (company, role, folder_path, created_at, job_description))
        else:
            cursor.execute('''
                INSERT INTO applications (company_name, role_name, folder_path, job_description)
                VALUES (?, ?, ?, ?)
            ''', (company, role, folder_path, job_description))
        app_id = cursor.lastrowid
        conn.commit()
        return app_id
    finally:
        conn.close()

def get_applications(search_query=None, sort_by="created_at", sort_order="DESC"):
    """Fetches all applications, optionally filtered and sorted."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Validate sort_order against whitelist to prevent SQL injection
        sort_order = sort_order.upper()
        if sort_order not in ("ASC", "DESC"):
            sort_order = "DESC"
        
        # Map friendly sort names to column names
        sort_map = {
            "Date": "created_at",
            "Company": "company_name",
            "Role": "role_name",
            "Status": "status"
        }
        column = sort_map.get(sort_by, "created_at")
        
        query_str = 'SELECT * FROM applications'
        params = []
        
        if search_query:
            query_str += " WHERE company_name LIKE ? ESCAPE '\\' OR role_name LIKE ? ESCAPE '\\'"
            escaped_search = search_query.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
            search_val = f"%{escaped_search}%"
            params.extend([search_val, search_val])
        
        if column == "status":
            query_str += f""" ORDER BY 
                CASE status
                    WHEN 'Applied' THEN 1
                    WHEN 'OA' THEN 2
                    WHEN 'HR Call' THEN 3
                    WHEN 'Interviewed' THEN 4
                    WHEN 'Offer' THEN 5
                    WHEN 'Rejected' THEN 6
                    WHEN 'Ghosted' THEN 7
                    ELSE 8
                END {sort_order}
            """
        else:
            query_str += f' ORDER BY {column} {sort_order}'
        
        cursor.execute(query_str, params)
        apps = cursor.fetchall()
        return apps
    finally:
        conn.close()

def get_stats():
    """Returns application statistics."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM applications')
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM applications WHERE status IN ('Interviewed', 'HR Call', 'OA')")
        interviewing = cursor.fetchone()[0]
        
        return total, interviewing
    finally:
        conn.close()

def update_application_status(app_id, status):
    """Updates the status of an application."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('UPDATE applications SET status = ? WHERE id = ?', (status, app_id))
        conn.commit()
    finally:
        conn.close()

def update_application_paths(app_id, company_name, role_name, folder_path):
    """Updates the company, role, and folder path for an existing application."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE applications 
            SET company_name = ?, role_name = ?, folder_path = ? 
            WHERE id = ?
        ''', (company_name, role_name, folder_path, app_id))
        conn.commit()
    finally:
        conn.close()

# This function helps the app find a specific job application using its unique ID number.
def get_application_by_id(app_id):
    """Fetches a single application by its ID."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM applications WHERE id = ?', (app_id,))
        app = cursor.fetchone()
        return app
    finally:
        conn.close()

def update_application_date(app_id, created_at):
    """Updates the creation date of an application."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('UPDATE applications SET created_at = ? WHERE id = ?', (created_at, app_id))
        conn.commit()
    finally:
        conn.close()

def add_interview(app_id, notes):
    """Adds a new interview record with incremental sequence. Returns the sequence number."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Atomic sequence generation — avoids race conditions with concurrent access
        cursor.execute('''
            INSERT INTO interviews (app_id, sequence, notes)
            VALUES (?, COALESCE((SELECT MAX(sequence) FROM interviews WHERE app_id = ?) + 1, 1), ?)
        ''', (app_id, app_id, notes))
        
        # Fetch the actual sequence value that was inserted
        cursor.execute('SELECT sequence FROM interviews WHERE rowid = ?', (cursor.lastrowid,))
        next_sequence = cursor.fetchone()[0]
        
        conn.commit()
        return next_sequence
    finally:
        conn.close()

def get_interviews(app_id):
    """Fetches all interviews for a specific application."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM interviews WHERE app_id = ? ORDER BY sequence ASC', (app_id,))
        interviews = cursor.fetchall()
        return interviews
    finally:
        conn.close()

def application_exists(company, role):
    """Checks if an application with the same company and role already exists."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM applications WHERE company_name = ? AND role_name = ?', (company, role))
        exists = cursor.fetchone() is not None
        return exists
    finally:
        conn.close()

def count_applications_with_name(company, role):
    """Counts how many applications exist for a company where the role name starts with 'role'."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Escape SQL LIKE wildcards in the role name to avoid false matches
        escaped_role = role.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        pattern = f"{escaped_role}%"
        cursor.execute("SELECT COUNT(*) FROM applications WHERE company_name = ? AND role_name LIKE ? ESCAPE '\\'", (company, pattern))
        count = cursor.fetchone()[0]
        return count
    finally:
        conn.close()

def delete_application(app_id):
    """Deletes an application record from the database."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM applications WHERE id = ?', (app_id,))
        conn.commit()
    finally:
        conn.close()

def remove_duplicates():
    """Removes duplicate records based on folder_path, keeping the one with the lowest ID."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Find all folder_paths that appear more than once
        cursor.execute('''
            SELECT folder_path, COUNT(*) 
            FROM applications 
            GROUP BY folder_path 
            HAVING COUNT(*) > 1
        ''')
        duplicates = cursor.fetchall()
        
        removed_count = 0
        for row in duplicates:
            path = row['folder_path']
            # Keep the record with the smallest ID, delete others
            cursor.execute('''
                DELETE FROM applications 
                WHERE folder_path = ? AND id NOT IN (
                    SELECT MIN(id) FROM applications WHERE folder_path = ?
                )
            ''', (path, path))
            removed_count += cursor.rowcount
                
        conn.commit()
        return removed_count
    finally:
        conn.close()

def get_analytics_data(start_date=None, end_date=None):
    """
    Fetches analytics data for the given date range.
    Returns:
        status_counts: dict {status: count}
        daily_counts: list of (date_str, count) sorted by date
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # 1. Status Counts
        query = "SELECT status, COUNT(*) FROM applications"
        params = []
        
        if start_date and end_date:
            query += " WHERE date(created_at) BETWEEN ? AND ?"
            params.extend([start_date, end_date])
            
        query += " GROUP BY status"
        
        cursor.execute(query, params)
        status_counts = {row[0]: row[1] for row in cursor.fetchall()}
        
        # 2. Daily Counts (Applications over time)
        # We strip the time part to group by day
        query = "SELECT date(created_at) as day, COUNT(*) FROM applications"
        params = []
        
        if start_date and end_date:
            query += " WHERE date(created_at) BETWEEN ? AND ?"
            params.extend([start_date, end_date])
            
        query += " GROUP BY day ORDER BY day ASC"
        
        cursor.execute(query, params)
        daily_counts = cursor.fetchall() # Returns list of (day, count)
        
        return status_counts, daily_counts
    finally:
        conn.close()

def get_daily_status_counts(start_date=None, end_date=None):
    """
    Fetches daily counts broken down by status.
    Returns: list of (date_str, status, count) sorted by date
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        
        # Query to group by both Day and Status
        # This prepares data for a Stacked Bar Chart, or Multi-Line Chart.
        # We want to know: "On Jan 1st, how many 'Rejected', how many 'Applied'?"
        query = "SELECT date(created_at) as day, status, COUNT(*) FROM applications"
        params = []
        
        if start_date and end_date:
            query += " WHERE date(created_at) BETWEEN ? AND ?"
            params.extend([start_date, end_date])
            
        query += " GROUP BY day, status ORDER BY day ASC"
        
        cursor.execute(query, params)
        data = cursor.fetchall()
        return data
    finally:
        conn.close()

def get_detailed_analytics(start_date=None, end_date=None, progress_callback=None):
    """
    Returns a detailed drill-down of application stats for the reporting view.
    Includes:
    - Total Count
    - Interviews Secured (Count of apps that have ANY interview logs)
    - By Company (Top 10)
    - By Role (Top 10)
    - By Status
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        params = []
        base_where = ""
        if start_date and end_date:
            base_where = " WHERE date(created_at) BETWEEN ? AND ?"
            params.extend([start_date, end_date])

        metrics = {
            "total_apps": 0,
            "interviews_secured": 0, # Reached Interview stage (Interviewed or Offer)
            "oa_count": 0,
            "hr_call_count": 0,
            "interviewed_count": 0,
            "offers_count": 0,
            "oa_roles_list": [],
            "hr_call_roles_list": [],
            "interview_roles_list": [],
            "by_company": [],
            "by_role": [],
            "by_status": []
        }

        # 1. Total Applications Count
        cursor.execute(f"SELECT COUNT(*) FROM applications{base_where}", params)
        metrics["total_apps"] = cursor.fetchone()[0]

        # 2. Granular Status Counts (Current Status)
        cursor.execute(f"SELECT status, COUNT(*) FROM applications{base_where} GROUP BY status", params)
        status_dict = {row[0]: row[1] for row in cursor.fetchall()}
        
        metrics["oa_count"] = status_dict.get("OA", 0)
        metrics["hr_call_count"] = status_dict.get("HR Call", 0)
        metrics["interviewed_count"] = status_dict.get("Interviewed", 0)
        metrics["offers_count"] = status_dict.get("Offer", 0)

        # 3. Interviews Secured
        query_interviews = f"""
            SELECT COUNT(DISTINCT a.id) 
            FROM applications a
            LEFT JOIN interviews i ON a.id = i.app_id
            {base_where} {' AND ' if base_where else ' WHERE '} (a.status IN ('Interviewed', 'Offer') OR i.id IS NOT NULL)
            AND a.status NOT IN ('OA', 'HR Call')
        """
        cursor.execute(query_interviews, params)
        metrics["interviews_secured"] = cursor.fetchone()[0]
        
        # 4a. List of OA Roles
        cursor.execute(f"SELECT company_name, role_name FROM applications{base_where} {' AND ' if base_where else ' WHERE '} status = 'OA' ORDER BY company_name ASC", params)
        metrics["oa_roles_list"] = cursor.fetchall()

        # 4b. List of HR Call Roles
        cursor.execute(f"SELECT company_name, role_name FROM applications{base_where} {' AND ' if base_where else ' WHERE '} status = 'HR Call' ORDER BY company_name ASC", params)
        metrics["hr_call_roles_list"] = cursor.fetchall()

        # 4c. List of specific roles that had interviews
        query_roles_list = f"""
            SELECT DISTINCT a.company_name, a.role_name
            FROM applications a
            LEFT JOIN interviews i ON a.id = i.app_id
            {base_where} {" AND " if base_where else " WHERE "} (a.status IN ('Interviewed', 'Offer') OR i.id IS NOT NULL)
            AND a.status NOT IN ('OA', 'HR Call')
            ORDER BY a.company_name ASC
        """
        cursor.execute(query_roles_list, params)
        metrics["interview_roles_list"] = cursor.fetchall()

        # 5. Frequency Breakdown by Company
        query_company = f"SELECT company_name, COUNT(*) as c FROM applications{base_where} GROUP BY company_name ORDER BY c DESC"
        cursor.execute(query_company, params)
        metrics["by_company"] = cursor.fetchall()

        # 6. Frequency Breakdown by Role Name
        query_role = f"SELECT role_name, COUNT(*) as c FROM applications{base_where} GROUP BY role_name"
        cursor.execute(query_role, params)
        raw_roles = cursor.fetchall()
        
        role_counts = {}
        total_roles = len(raw_roles)
        for i, (role_name, count) in enumerate(raw_roles):
            category = get_mapped_role(role_name)
            role_counts[category] = role_counts.get(category, 0) + count
            if progress_callback:
                progress_callback(i + 1, total_roles, role_name)
            
        # Convert and sort descending
        metrics["by_role"] = sorted(role_counts.items(), key=lambda x: x[1], reverse=True)

        # 7. Application Status Distribution
        query_status = f"SELECT status, COUNT(*) as c FROM applications{base_where} GROUP BY status ORDER BY c DESC"
        cursor.execute(query_status, params)
        metrics["by_status"] = cursor.fetchall()

        return metrics
    finally:
        conn.close()

def get_all_role_mappings():
    """Returns all rows in the role_mappings table."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT original_role, mapped_category FROM role_mappings ORDER BY original_role ASC')
        mappings = cursor.fetchall()
        return mappings
    finally:
        conn.close()

def update_role_mapping(original_role, new_category):
    """Manually updates the category for a specific role."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO role_mappings (original_role, mapped_category) 
            VALUES (?, ?) 
            ON CONFLICT(original_role) DO UPDATE SET mapped_category=excluded.mapped_category
        ''', (original_role, new_category))
        conn.commit()
    finally:
        conn.close()
    
def clear_all_role_mappings():
    """Clears the mapping cache so the LLM will re-classify all roles next time."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM role_mappings')
        conn.commit()
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
