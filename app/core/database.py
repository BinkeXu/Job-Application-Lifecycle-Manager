import sqlite3
import os
from datetime import datetime

from .config_mgr import get_active_root

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
    
    return conn

# This "Initializes" the database by creating tables if they don't exist.
def init_db():
    """Initializes the database with the required tables."""
    conn = get_db_connection()
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

    conn.commit()
    conn.close()

def add_application(company, role, folder_path, created_at=None, job_description=None):
    """Inserts a new application record."""
    conn = get_db_connection()
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
    conn.close()
    return app_id

def get_applications(search_query=None, sort_by="created_at", sort_order="DESC"):
    """Fetches all applications, optionally filtered and sorted."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Map friendly sort names to column names
    sort_map = {
        "Date": "created_at",
        "Company": "company_name"
    }
    column = sort_map.get(sort_by, "created_at")
    
    query_str = 'SELECT * FROM applications'
    params = []
    
    if search_query:
        query_str += ' WHERE company_name LIKE ? OR role_name LIKE ?'
        search_val = f"%{search_query}%"
        params.extend([search_val, search_val])
    
    query_str += f' ORDER BY {column} {sort_order}'
    
    cursor.execute(query_str, params)
    apps = cursor.fetchall()
    conn.close()
    return apps

def get_stats():
    """Returns application statistics."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM applications')
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM applications WHERE status = 'Interviewing'")
    interviewing = cursor.fetchone()[0]
    
    conn.close()
    return total, interviewing

def update_application_status(app_id, status):
    """Updates the status of an application."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE applications SET status = ? WHERE id = ?', (status, app_id))
    conn.commit()
    conn.close()

# This function helps the app find a specific job application using its unique ID number.
def get_application_by_id(app_id):
    """Fetches a single application by its ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM applications WHERE id = ?', (app_id,))
    app = cursor.fetchone()
    conn.close()
    return app

def update_application_date(app_id, created_at):
    """Updates the creation date of an application."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE applications SET created_at = ? WHERE id = ?', (created_at, app_id))
    conn.commit()
    conn.close()

def add_interview(app_id, notes):
    """Adds a new interview record with incremental sequence. Returns the sequence number."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get current sequence
    cursor.execute('SELECT COUNT(*) FROM interviews WHERE app_id = ?', (app_id,))
    count = cursor.fetchone()[0]
    next_sequence = count + 1
    
    cursor.execute('''
        INSERT INTO interviews (app_id, sequence, notes)
        VALUES (?, ?, ?)
    ''', (app_id, next_sequence, notes))
    
    conn.commit()
    conn.close()
    return next_sequence

def get_interviews(app_id):
    """Fetches all interviews for a specific application."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM interviews WHERE app_id = ? ORDER BY sequence ASC', (app_id,))
    interviews = cursor.fetchall()
    conn.close()
    return interviews

def application_exists(company, role):
    """Checks if an application with the same company and role already exists."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM applications WHERE company_name = ? AND role_name = ?', (company, role))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def count_applications_with_name(company, role):
    """Counts how many applications exist for a company where the role name starts with 'role'."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Looking for exact match or 'Role (Index)' format
    pattern = f"{role}%"
    cursor.execute('SELECT COUNT(*) FROM applications WHERE company_name = ? AND role_name LIKE ?', (company, pattern))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def delete_application(app_id):
    """Deletes an application record from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Enable foreign keys for cascade delete
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute('DELETE FROM applications WHERE id = ?', (app_id,))
    conn.commit()
    conn.close()

def remove_duplicates():
    """Removes duplicate records based on folder_path, keeping the one with the lowest ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Enable foreign keys for cascade delete
    cursor.execute("PRAGMA foreign_keys = ON")
    
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
    conn.close()
    return removed_count

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
