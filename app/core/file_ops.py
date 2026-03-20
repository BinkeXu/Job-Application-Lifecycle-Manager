import os
import shutil
from pathlib import Path
from .config_mgr import load_config, get_active_root

def create_application_folder(company, role, job_description=None, cv_template_path=None):
    """
    Creates a folder for a new job application and copies templates.
    Also saves the job description as a text file if provided.
    
    Args:
        company (str): Name of the company.
        role (str): Job role/title.
        job_description (str, optional): Text of the job description.
        cv_template_path (str, optional): Overrides the default CV template if provided.
        
    Returns:
        tuple: (Absolute path to the created folder, creation timestamp).
    """
    config = load_config()
    root_path = get_active_root()
    if not root_path:
        raise ValueError("Active root directory is not set.")
        
    root_dir = Path(root_path)
    
    # Use selected CV template or default from config
    cv_template = Path(cv_template_path) if cv_template_path else Path(config.get("cv_template_path"))
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

def write_jalm_id(folder_path, app_id):
    """Writes the database application ID to a hidden .jalm_id file in the folder."""
    import os
    id_file = Path(folder_path) / ".jalm_id"
    with open(id_file, "w", encoding="utf-8") as f:
        f.write(str(app_id))
    
    # Try to hide the file on Windows
    if os.name == 'nt':
        import ctypes
        try:
            FILE_ATTRIBUTE_HIDDEN = 0x02
            ctypes.windll.kernel32.SetFileAttributesW(str(id_file), FILE_ATTRIBUTE_HIDDEN)
        except Exception:
            pass

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
    Performs 'Status Discovery' by checking for key files (like interviews.txt).
    Returns a list of application metadata including a 'has_interviews' flag.
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
                    # Check for indicators of application status on disk
                    has_interviews = (role_dir / "interviews.txt").exists()
                    
                    # Read .jalm_id if it exists
                    jalm_id = None
                    id_file = role_dir / ".jalm_id"
                    if id_file.exists():
                        try:
                            with open(id_file, "r", encoding="utf-8") as f:
                                content = f.read().strip()
                                if content.isdigit():
                                    jalm_id = int(content)
                        except Exception:
                            pass

                    found_apps.append({
                        'company': company_dir.name,
                        'role': role_dir.name,
                        'path': str(role_dir.absolute()),
                        'created_at': get_folder_creation_time(role_dir),
                        'has_interviews': has_interviews,
                        'jalm_id': jalm_id
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

