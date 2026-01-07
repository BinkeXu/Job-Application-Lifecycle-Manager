import os
import shutil
from pathlib import Path
from .config_mgr import load_config

def create_application_folder(company, role):
    """
    Creates a folder for a new job application and copies templates.
    Returns the absolute path to the created folder.
    """
    config = load_config()
    root_dir = Path(config.get("root_directory"))
    cv_template = Path(config.get("cv_template_path"))
    cl_template = Path(config.get("cl_template_path"))

    if not root_dir.exists():
        raise FileNotFoundError(f"Root directory does not exist: {root_dir}")

    # Create Company/Role folder structure
    # Sanitize names for folder paths
    company_clean = "".join(c for c in company if c.isalnum() or c in (' ', '_', '-')).strip()
    role_clean = "".join(c for c in role if c.isalnum() or c in (' ', '_', '-')).strip()
    
    app_folder = root_dir / company_clean / role_clean
    app_folder.mkdir(parents=True, exist_ok=True)

    # Copy and rename templates
    if cv_template.exists():
        cv_dest = app_folder / f"{company_clean}_{role_clean}_CV{cv_template.suffix}"
        shutil.copy2(cv_template, cv_dest)
    
    if cl_template.exists():
        cl_dest = app_folder / f"{company_clean}_{role_clean}_CL{cl_template.suffix}"
        shutil.copy2(cl_template, cl_dest)

    return str(app_folder.absolute())

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
                        'path': str(role_dir.absolute())
                    })
    return found_apps

