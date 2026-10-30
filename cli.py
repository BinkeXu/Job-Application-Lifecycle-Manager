#!/usr/bin/env python3
"""
Job Application Lifecycle Manager (JALM) - CLI Interface
Provides headless command-line access to JALM for users, automation scripts,
and LLM agents (e.g. Antigravity, Cursor, Claude Code).
"""

import sys
import os
import json
import argparse
from pathlib import Path

# Ensure application modules can be resolved
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config_mgr import load_config, get_active_root
from app.core.database import (
    init_db, add_application, get_applications, get_application_by_id,
    update_application_status, update_application_job_description,
    application_exists, count_applications_with_name, get_stats, get_interviews
)
from app.core.file_ops import create_application_folder, write_jalm_id, save_job_description_file

VALID_STATUSES = ["Applied", "OA", "HR Call", "Interviewed", "Offer", "Rejected", "Ghosted"]

def _find_document_files(folder_path):
    """Discovers CV, Cover Letter, and JD files in the folder."""
    files = {"cv_path": None, "cover_letter_path": None, "jd_path": None}
    if not folder_path or not os.path.exists(folder_path):
        return files

    p = Path(folder_path)
    for f in p.iterdir():
        if not f.is_file():
            continue
        name_lower = f.name.lower()
        if "cv" in name_lower and f.suffix.lower() in (".docx", ".pdf"):
            files["cv_path"] = str(f.absolute())
        elif "cover" in name_lower and f.suffix.lower() in (".docx", ".pdf"):
            files["cover_letter_path"] = str(f.absolute())
        elif f.name.lower() == "job_description.txt":
            files["jd_path"] = str(f.absolute())

    return files

def handle_add(args):
    init_db()
    company = args.company.strip()
    role = args.role.strip()

    if not company or not role:
        print("[ERROR] Company name and role title cannot be empty.", file=sys.stderr)
        return 1

    # Resolve Job Description
    jd_content = ""
    if args.jd_file:
        if not os.path.exists(args.jd_file):
            print(f"[ERROR] Job description file not found: {args.jd_file}", file=sys.stderr)
            return 1
        with open(args.jd_file, "r", encoding="utf-8") as f:
            jd_content = f.read().strip()
    elif args.jd:
        jd_content = args.jd.strip()

    # Resolve CV Template
    cv_template_path = None
    if args.template:
        config = load_config()
        additionals = config.get("additional_cv_templates", {})
        if args.template in additionals:
            cv_template_path = additionals[args.template]
        elif os.path.exists(args.template):
            cv_template_path = args.template
        else:
            print(f"[ERROR] Template '{args.template}' not found in configuration or filesystem.", file=sys.stderr)
            return 1

    # Check for duplicates
    final_role = role
    if application_exists(company, role):
        if args.index:
            count = count_applications_with_name(company, role)
            final_role = f"{role} ({count + 1})"
        elif not args.force:
            msg = f"Application for '{company} - {role}' already exists. Use --index to auto-increment, or --force to create anyway."
            if args.json:
                print(json.dumps({"status": "error", "message": msg}))
            else:
                print(f"[ERROR] {msg}", file=sys.stderr)
            return 1

    try:
        # 1. Create folder and clone templates
        folder_path, creation_time = create_application_folder(
            company=company,
            role=final_role,
            job_description=jd_content if jd_content else None,
            cv_template_path=cv_template_path
        )

        # 2. Add to database
        app_id = add_application(
            company=company,
            role=final_role,
            folder_path=folder_path,
            created_at=creation_time,
            job_description=jd_content if jd_content else None
        )

        # 3. Write hidden tracking ID
        write_jalm_id(folder_path, app_id)

        # 4. Find paths to generated documents
        docs = _find_document_files(folder_path)

        result = {
            "status": "success",
            "id": app_id,
            "company": company,
            "role": final_role,
            "folder_path": folder_path,
            "cv_path": docs["cv_path"],
            "cover_letter_path": docs["cover_letter_path"],
            "jd_path": docs["jd_path"],
            "created_at": str(creation_time)
        }

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"[SUCCESS] Created application #{app_id}: {company} - {final_role}")
            print(f"Folder:       {folder_path}")
            if docs["cv_path"]:
                print(f"CV:           {docs['cv_path']}")
            if docs["cover_letter_path"]:
                print(f"Cover Letter: {docs['cover_letter_path']}")
            if docs["jd_path"]:
                print(f"JD File:      {docs['jd_path']}")

        return 0
    except Exception as e:
        if args.json:
            print(json.dumps({"status": "error", "message": str(e)}))
        else:
            print(f"[ERROR] Failed to create application: {e}", file=sys.stderr)
        return 1

def handle_list(args):
    init_db()
    apps = get_applications(search_query=args.search)

    if args.status:
        apps = [a for a in apps if a.get("status") == args.status]

    if args.limit and args.limit > 0:
        apps = apps[:args.limit]

    if args.json:
        print(json.dumps(apps, indent=2))
        return 0

    if not apps:
        print("No applications found.")
        return 0

    header = f"{'ID':<6} {'Company':<25} {'Role':<30} {'Status':<14} {'Date':<12}"
    print(header)
    print("-" * len(header))
    for a in apps:
        date_str = (a.get("created_at") or "").split(" ")[0]
        print(f"{a['id']:<6} {a['company_name'][:24]:<25} {a['role_name'][:29]:<30} {a['status']:<14} {date_str:<12}")

    return 0

def handle_get(args):
    init_db()
    app = get_application_by_id(args.id)
    if not app:
        if args.json:
            print(json.dumps({"status": "error", "message": f"Application #{args.id} not found."}))
        else:
            print(f"[ERROR] Application #{args.id} not found.", file=sys.stderr)
        return 1

    docs = _find_document_files(app.get("folder_path"))
    interviews = get_interviews(args.id)

    app_detail = {
        **app,
        "cv_path": docs["cv_path"],
        "cover_letter_path": docs["cover_letter_path"],
        "jd_path": docs["jd_path"],
        "interviews": interviews
    }

    if args.json:
        print(json.dumps(app_detail, indent=2))
        return 0

    print(f"Application #{app['id']}: {app['company_name']} - {app['role_name']}")
    print(f"Status:       {app['status']}")
    print(f"Applied Date: {app['created_at']}")
    print(f"Folder:       {app['folder_path']}")
    print(f"CV:           {docs['cv_path'] or 'None'}")
    print(f"Cover Letter: {docs['cover_letter_path'] or 'None'}")
    print(f"Interviews:   {len(interviews)} logged")
    print("\n--- Job Description ---")
    print(app.get("job_description") or "(No job description saved)")

    return 0

def handle_set_status(args):
    init_db()
    if args.status not in VALID_STATUSES:
        msg = f"Invalid status '{args.status}'. Must be one of: {', '.join(VALID_STATUSES)}"
        if args.json:
            print(json.dumps({"status": "error", "message": msg}))
        else:
            print(f"[ERROR] {msg}", file=sys.stderr)
        return 1

    app = get_application_by_id(args.id)
    if not app:
        msg = f"Application #{args.id} not found."
        if args.json:
            print(json.dumps({"status": "error", "message": msg}))
        else:
            print(f"[ERROR] {msg}", file=sys.stderr)
        return 1

    update_application_status(args.id, args.status)
    if args.json:
        print(json.dumps({"status": "success", "id": args.id, "new_status": args.status}))
    else:
        print(f"[SUCCESS] Application #{args.id} status updated to '{args.status}'.")

    return 0

def handle_set_jd(args):
    init_db()
    app = get_application_by_id(args.id)
    if not app:
        msg = f"Application #{args.id} not found."
        if args.json:
            print(json.dumps({"status": "error", "message": msg}))
        else:
            print(f"[ERROR] {msg}", file=sys.stderr)
        return 1

    content = ""
    if args.jd_file:
        if not os.path.exists(args.jd_file):
            print(f"[ERROR] File not found: {args.jd_file}", file=sys.stderr)
            return 1
        with open(args.jd_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
    elif args.jd:
        content = args.jd.strip()

    update_application_job_description(args.id, content)
    folder_path = app.get("folder_path")
    if folder_path and os.path.exists(folder_path):
        save_job_description_file(folder_path, content)

    if args.json:
        print(json.dumps({"status": "success", "id": args.id, "jd_length": len(content)}))
    else:
        print(f"[SUCCESS] Updated Job Description for Application #{args.id} ({len(content)} characters).")

    return 0

def handle_stats(args):
    init_db()
    total, active = get_stats()
    
    # Read ghosted count if analytics.json exists in active root
    ghosted = 0
    root = get_active_root()
    if root:
        an_file = os.path.join(root, "analytics.json")
        if os.path.exists(an_file):
            try:
                with open(an_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    ghosted = data.get("Ghosted", 0)
            except Exception:
                pass

    stats_data = {
        "total_applications": total,
        "active_interviews": active,
        "ghosted_30d": ghosted,
        "active_root": root
    }

    if args.json:
        print(json.dumps(stats_data, indent=2))
    else:
        print("=== JALM Workspace Stats ===")
        print(f"Applications Root: {root or '(None)'}")
        print(f"Total Apps:        {total}")
        print(f"Active (OA/HR/Int):{active}")
        print(f"Ghosted (30d+):    {ghosted}")

    return 0

def build_parser():
    parser = argparse.ArgumentParser(
        prog="jalm",
        description="Job Application Lifecycle Manager (JALM) - Command Line Interface"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: add
    p_add = subparsers.add_parser("add", help="Create a new job application")
    p_add.add_argument("-c", "--company", required=True, help="Company name")
    p_add.add_argument("-r", "--role", required=True, help="Role title")
    p_add.add_argument("--jd", help="Job description raw text string")
    p_add.add_argument("--jd-file", help="Path to file containing job description")
    p_add.add_argument("-t", "--template", help="Specific CV template name or path")
    p_add.add_argument("--index", action="store_true", help="Auto-increment index if duplicate role exists")
    p_add.add_argument("--force", action="store_true", help="Force creation even if duplicate exists")
    p_add.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    # Command: list
    p_list = subparsers.add_parser("list", help="List applications")
    p_list.add_argument("-n", "--limit", type=int, default=20, help="Maximum items to return (default: 20)")
    p_list.add_argument("-s", "--search", help="Search query (company or role)")
    p_list.add_argument("--status", help="Filter by status")
    p_list.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    # Command: get
    p_get = subparsers.add_parser("get", help="Get application details by ID")
    p_get.add_argument("id", type=int, help="Application ID")
    p_get.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    # Command: set-status
    p_status = subparsers.add_parser("set-status", help="Update application status")
    p_status.add_argument("id", type=int, help="Application ID")
    p_status.add_argument("status", help="New status")
    p_status.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    # Command: set-jd
    p_jd = subparsers.add_parser("set-jd", help="Update application job description")
    p_jd.add_argument("id", type=int, help="Application ID")
    p_jd.add_argument("--jd", help="Raw job description text")
    p_jd.add_argument("--jd-file", help="Path to file containing job description")
    p_jd.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    # Command: stats
    p_stats = subparsers.add_parser("stats", help="View workspace statistics")
    p_stats.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    return parser

def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    commands = {
        "add": handle_add,
        "list": handle_list,
        "get": handle_get,
        "set-status": handle_set_status,
        "set-jd": handle_set_jd,
        "stats": handle_stats
    }

    handler = commands.get(args.command)
    if handler:
        return handler(args)
    return 1

if __name__ == "__main__":
    sys.exit(main())
