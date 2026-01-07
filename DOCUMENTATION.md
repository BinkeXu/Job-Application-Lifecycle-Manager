# JALM Technical Documentation

This document provides a detailed overview of the Job Application Lifecycle Manager (JALM) architecture, data models, and core logic.

## 🏗️ Project Architecture

JALM follows a modular Python structure:

```text
Job Application Manager/
├── app/
│   ├── core/           # Business logic and data management
│   │   ├── config_mgr.py
│   │   ├── database.py
│   │   └── file_ops.py
│   ├── gui/            # UI components and windows
│   │   ├── dashboard.py
│   │   ├── setup_wizard.py
│   │   ├── add_app_dialog.py
│   │   └── interview_manager.py
│   ├── utils/          # Helper utilities
│   │   └── tooltip.py
│   └── models/         # (Future growth for ORM/Dataclasses)
├── main.py             # Entry point
├── config.json         # User settings (Generated)
└── applications.db     # SQLite database (Generated)
```

## 🗄️ Database Schema

JALM uses SQLite for persistent storage.

### Table: `applications`
Stores the high-level metadata for each job application.

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | INTEGER | Primary Key. |
| `company_name` | TEXT | Name of the company. |
| `role_name` | TEXT | Specific job title. |
| `folder_path` | TEXT | Absolute path to the role folder. |
| `status` | TEXT | Applied, Interviewing, Rejected, Offer, Ghosted. |
| `created_at` | DATETIME | Timestamp of entry creation. |

### Table: `interviews`
Stores notes related to specific interview rounds.

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | INTEGER | Primary Key. |
| `app_id` | INTEGER | Foreign Key referencing `applications.id`. |
| `sequence` | INTEGER | The interview number (1, 2, 3, etc.). |
| `notes` | TEXT | Interview details and feedback. |
| `date` | DATETIME | Timestamp of interview log. |

## ⚙️ Core Modules

### Configuration Management (`config_mgr.py`)
Handles loading and saving user paths (root directory and templates) from `config.json`. It provides a validation check (`is_config_complete`) used at startup to determine if the Setup Wizard is needed.

### File Operations (`file_ops.py`)
Contains the logic for:
- Creating hierarchical folder structures (`Root/Company/Role`).
- Cloning and renaming template files using `shutil`.
- Scanning the filesystem for existing `Company/Role` directories to facilitate migration.

### Performance Optimizations
- **Debouncing**: Implemented in `Dashboard` using `widget.after()`. Rapid typing in the search bar won't trigger database queries until a 300ms pause is detected.
- **Batch Rendering**: The `Dashboard` renders application items in chunks of 15 using a recursive `_render_chunk` call. This prevents the Main Loop from locking up when displaying hundreds of rows.

## 🎨 UI Framework

The application is built using `CustomTkinter`, a wrapper around `tkinter` that provides a modern, high-DPI compatible interface.

- **SetupWizard**: A modal window for initial configuration.
- **Dashboard**: The primary interface, utilizing `CTkScrollableFrame` for the application list.
- **ToolTip**: A custom utility in `app/utils` that provides hover-based information for truncated text.

## 🛠️ Error Handling

- **Folder Integrity**: The `AppListItem` checks for the existence of the `folder_path` on every refresh. If the folder is moved or deleted outside JALM, the "Open Folder" button is replaced with a "Path Missing" warning.
- **Database Safety**: Uses SQLite's `ON DELETE CASCADE` to ensure that deleting an application (future feature) would remove related interviews.
