import os
import shutil
from pathlib import Path
from .config_mgr import load_config, get_active_root

def create_application_folder(company, role, job_description=None):
    """
    Creates a folder for a new job application and copies templates.
    Also saves the job description as a text file if provided.
    Returns the absolute path to the created folder.
    """
    config = load_config()
    root_path = get_active_root()
    if not root_path:
        raise ValueError("Active root directory is not set.")
        
    root_dir = Path(root_path)
    cv_template = Path(config.get("cv_template_path"))
    cover_letter_template = Path(config.get("cover_letter_template_path"))

    if not root_dir.exists():
        raise FileNotFoundError(f"Root directory does not exist: {root_dir}")

    # Create Company/Role folder structure
    # Sanitize names for folder paths
    company_clean = "".join(c for c in company if c.isalnum() or c in (' ', '_', '-')).strip()
    role_clean = "".join(c for c in role if c.isalnum() or c in (' ', '_', '-')).strip()
    
    app_folder = root_dir / company_clean / role_clean
    app_folder.mkdir(parents=True, exist_ok=True)

    # Copy and rename templates
    user_name = config.get("user_name", "User")
    if cv_template.exists():
        cv_dest = app_folder / f"{user_name}_CV_{role_clean}{cv_template.suffix}"
        shutil.copy2(cv_template, cv_dest)
    
    if cover_letter_template.exists():
        cl_dest = app_folder / f"{user_name}_Cover Letter_{role_clean}{cover_letter_template.suffix}"
        shutil.copy2(cover_letter_template, cl_dest)

    # Save Job Description
    if job_description:
        jd_path = app_folder / "job_description.txt"
        with open(jd_path, "w", encoding="utf-8") as f:
            f.write(job_description)

    creation_time = get_folder_creation_time(str(app_folder.absolute()))
    return str(app_folder.absolute()), creation_time

def get_folder_creation_time(path):
    """Returns the creation time of a folder formatted for SQLite."""
    import time
    from datetime import datetime
    
    # On Windows, st_ctime is the creation time
    # On Unix, st_ctime is the metadata change time
    # Since the user is on Windows, this is correct for creation time
    ctime = os.path.getctime(path)
    return datetime.fromtimestamp(ctime).strftime('%Y-%m-%d %H:%M:%S')

def open_folder(path):
    """Opens the folder in the system's file explorer."""
    if os.name == 'nt':
        os.startfile(path)
    else:
        import subprocess
        subprocess.run(["open", path])

def scan_for_existing_applications(root_path):
    """
    Scans the root path for existing Company/Role folder structures.
    Returns a list of dicts: [{'company': '...', 'role': '...', 'path': '...'}]
    """
    root = Path(root_path)
    if not root.exists() or not root.is_dir():
        return []

    found_apps = []
    # Structure: Root / Company / Role
    for company_dir in root.iterdir():
        if company_dir.is_dir():
            for role_dir in company_dir.iterdir():
                if role_dir.is_dir():
                    found_apps.append({
                        'company': company_dir.name,
                        'role': role_dir.name,
                        'path': str(role_dir.absolute()),
                        'created_at': get_folder_creation_time(role_dir)
                    })
    return found_apps

def append_interview_note(folder_path, sequence, note):
    """Appends an interview note to interviews.txt in the application folder."""
    from datetime import datetime
    jd_path = Path(folder_path) / "interviews.txt"
    date_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    formatted_note = f"\n--- Interview {sequence} ({date_str}) ---\n{note}\n"
    
    with open(jd_path, "a", encoding="utf-8") as f:
        f.write(formatted_note)

