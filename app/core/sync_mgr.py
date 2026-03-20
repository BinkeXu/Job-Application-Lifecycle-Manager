import os
from .config_mgr import get_active_root
from .file_ops import scan_for_existing_applications, write_jalm_id
from .database import (
    add_application, get_applications, delete_application, remove_duplicates, 
    update_application_date, get_application_by_id, update_application_status,
    update_application_paths, application_exists
)

def sync_workspace(root_path):
    """
    Centralized logic to sync the filesystem with the database.
    Returns highly detailed status messages about what was done.
    """
    if not root_path:
        return 0, 0, 0, 0

    found_apps = scan_for_existing_applications(root_path)
    current_db_apps = get_applications()
    
    # Maps
    db_by_id = {app['id']: app for app in current_db_apps}
    db_by_key = {(app['company_name'], app['role_name']): app for app in current_db_apps}
    
    added_count = 0
    updated_count = 0
    
    # We will keep track of app IDs that exist on disk so we can delete missing ones later.
    active_ids = set()

    # Track jalm_ids we have seen in this scan to handle copied folders
    seen_jalm_ids = set()

    for app in found_apps:
        company = app['company']
        role = app['role']
        path = app['path']
        created_at = app.get('created_at')
        is_interviewed = app.get('has_interviews', False)
        jalm_id = app.get('jalm_id')

        target_app_id = None
        is_new = False
        
        # 1. Match by jalm_id
        if jalm_id is not None and jalm_id in db_by_id and jalm_id not in seen_jalm_ids:
            target_app_id = jalm_id
            seen_jalm_ids.add(jalm_id)
            db_record = db_by_id[target_app_id]
            
            # Check if path or names changed (Rename detection)
            if db_record['folder_path'] != path or db_record['company_name'] != company or db_record['role_name'] != role:
                update_application_paths(target_app_id, company, role, path)
                updated_count += 1
                
        # 2. Match by company/role fallback
        elif (company, role) in db_by_key:
            target_app_id = db_by_key[(company, role)]['id']
            # Write missing jalm_id
            write_jalm_id(path, target_app_id)
            if jalm_id is None:
                seen_jalm_ids.add(target_app_id)
                
        # 3. New Application
        else:
            is_new = True
            new_id = add_application(company, role, path, created_at)
            write_jalm_id(path, new_id)
            target_app_id = new_id
            added_count += 1
            if is_interviewed:
                update_application_status(target_app_id, 'Interviewed')
            
            seen_jalm_ids.add(target_app_id)
            
            # Since we added it, it's safe to say it's an active ID
            active_ids.add(target_app_id)
            continue # skip the update checks below for a brand new app

        # At this point, target_app_id is the matched record.
        active_ids.add(target_app_id)
        
        # Use pre-fetched record from db_by_id; only query DB for newly added records
        current_record = db_by_id.get(target_app_id)
        if current_record is None:
            current_record = get_application_by_id(target_app_id)
        
        # Update creation date if differs
        if current_record and current_record['created_at'] != created_at:
            update_application_date(target_app_id, created_at)
            updated_count += 1

        # Promote status
        if is_interviewed and current_record and current_record['status'] == 'Applied':
            update_application_status(target_app_id, 'Interviewed')
            updated_count += 1

    # Remove duplicates in DB (if any snuck in due to other bugs)
    duplicates_removed = remove_duplicates()

    # Check for missing folders and remove from DB
    removed_count = 0
    # Refetch since duplicates might be gone
    db_apps = get_applications()
    for app in db_apps:
        app_id = app['id']
        if app_id not in active_ids:
            if not os.path.exists(app['folder_path']):
                delete_application(app_id)
                removed_count += 1

    return added_count, updated_count, removed_count, duplicates_removed
