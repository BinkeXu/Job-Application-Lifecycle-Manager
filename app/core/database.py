import sqlite3
import os
from datetime import datetime

from .config_mgr import get_active_root

DB_NAME = "jalm_apps.db"

def get_db_connection():
    """Establishes a connection to the SQLite database inside the active root."""
    root = get_active_root()
    if not root:
        # Fallback for initialization or if root not set (managed by Main App)
        conn = sqlite3.connect(DB_NAME)
    else:
        db_path = os.path.join(root, DB_NAME)
        conn = sqlite3.connect(db_path)
        
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database with the required tables."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create applications table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            role_name TEXT NOT NULL,
            folder_path TEXT NOT NULL,
            status TEXT DEFAULT 'Applied',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create interviews table
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

    # Create Indexes for faster search
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_apps_company ON applications(company_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_apps_role ON applications(role_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_apps_created ON applications(created_at)')

    conn.commit()
    conn.close()

def add_application(company, role, folder_path):
    """Inserts a new application record."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO applications (company_name, role_name, folder_path)
        VALUES (?, ?, ?)
    ''', (company, role, folder_path))
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

def add_interview(app_id, notes):
    """Adds a new interview record with incremental sequence."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get current sequence
    cursor.execute('SELECT COUNT(*) FROM interviews WHERE app_id = ?', (app_id,))
    count = cursor.fetchone()[0]
    
    cursor.execute('''
        INSERT INTO interviews (app_id, sequence, notes)
        VALUES (?, ?, ?)
    ''', (app_id, count + 1, notes))
    
    conn.commit()
    conn.close()

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

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
