import os
import shutil
from pathlib import Path
from datetime import datetime

class BatchExporter:
    """
    Handles the bulk exportation of application documents (CVs and Job Descriptions).
    Integrates a 'best-guess' search logic to find files in application folders
    and renames them following a standardized sequence for professional organization.
    """
    def __init__(self):
        # Track counts and non-fatal errors during the operation
        self.stats = {
            "exported_cvs": 0,
            "exported_jds": 0,
            "errors": []
        }

    def export(self, applications, target_dir, search_query="", export_cv=True, export_jd=True):
        """
        Exports the selected document types for a list of applications to a target directory.
        
        Args:
            applications (list): List of application dicts from the database.
            target_dir (str): The destination directory chosen by the user.
            search_query (str): The role name used for naming the exported files.
            export_cv (bool): Enable/disable CV export.
            export_jd (bool): Enable/disable JD export.
        """
        target_path = Path(target_dir)
        if not target_path.exists():
            target_path.mkdir(parents=True, exist_ok=True)
            
        # SAFETY: If the target folder isn't empty, create a subfolder with a 
        # timestamp to prevent overwriting existing work or causing confusion.
        if any(target_path.iterdir()):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            target_path = target_path / f"Export_{timestamp}"
            target_path.mkdir()

        # Sequential numbering starts at 1 for each document type
        cv_index = 1
        jd_index = 1
        
        # Use the search query as the file prefix for the entire batch.
        # This aligns with the requirement to have a role-based naming pattern.
        file_prefix = search_query.strip() if search_query else "Application"
        
        # Strip illegal characters from the prefix to ensure file system compatibility.
        file_prefix = "".join(c for c in file_prefix if c.isalnum() or c in (' ', '_', '-')).strip()

        for app in applications:
            folder_path = Path(app['folder_path'])
            if not folder_path.exists():
                self.stats["errors"].append(f"Missing folder: {app['company_name']} - {app['role_name']}")
                continue

            # 1. Process CV
            if export_cv:
                # Find the most relevant CV/Resume file in the application folder.
                cv_file = self._find_best_cv(folder_path)
                if cv_file:
                    try:
                        ext = cv_file.suffix
                        # Format: [Role Name] cv [Index].[Extension]
                        new_name = f"{file_prefix} cv {cv_index}{ext}"
                        shutil.copy2(cv_file, target_path / new_name)
                        cv_index += 1
                        self.stats["exported_cvs"] += 1
                    except Exception as e:
                        self.stats["errors"].append(f"Failed to copy CV for {app['company_name']}: {str(e)}")

            # 2. Process JD
            if export_jd:
                # Find the Job Description file (usually job_description.txt).
                jd_file = self._find_jd(folder_path)
                if jd_file:
                    try:
                        ext = jd_file.suffix
                        # Format: [Role Name] jd [Index].[Extension]
                        new_name = f"{file_prefix} jd {jd_index}{ext}"
                        shutil.copy2(jd_file, target_path / new_name)
                        jd_index += 1
                        self.stats["exported_jds"] += 1
                    except Exception as e:
                        # Non-fatal error, skip if copying fail
                        pass
        
        return self.stats

    def _find_best_cv(self, folder_path):
        """
        Utility to identify the 'main' CV file in a folder.
        Prioritizes:
        1. Files containing 'CV' or 'Resume' (with high-confidence extensions).
        2. Files with a .pdf extension.
        3. Most recently modified file in case of multiple candidates.
        """
        candidates = []
        for item in folder_path.iterdir():
            # Skip hidden/temporary files created by Word or Windows
            if item.is_file() and not item.name.startswith("~"):
                name_lower = item.name.lower()
                if "cv" in name_lower or "resume" in name_lower:
                    if item.suffix.lower() in ['.pdf', '.docx', '.doc']:
                        candidates.append((10, item)) # Highest priority
                elif item.suffix.lower() == '.pdf':
                    candidates.append((5, item))   # Medium priority
        
        if not candidates:
            return None
            
        # Return the best match based on priority score then modification time
        candidates.sort(key=lambda x: (x[0], x[1].stat().st_mtime), reverse=True)
        return candidates[0][1]

    def _find_jd(self, folder_path):
        """
        Identifies the Job Description file.
        Commonly 'job_description.txt' created by JALM, but falls back to 
        searching for 'JD' or 'Description' in filenames.
        """
        jd_txt = folder_path / "job_description.txt"
        if jd_txt.exists():
            return jd_txt
            
        for item in folder_path.iterdir():
            if item.is_file():
                name_lower = item.name.lower()
                if ("jd" in name_lower or "description" in name_lower) and "job" in name_lower:
                     return item
        return None
