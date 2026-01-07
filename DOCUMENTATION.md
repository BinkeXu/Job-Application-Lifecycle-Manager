# JALM Technical Documentation

This document provides a detailed overview of the Job Application Lifecycle Manager (JALM) architecture, data models, and core logic.

## 🏗️ Project Architecture

JALM follows a modular Python structure:

```text
Job Application Lifecycle Manager/
├── app/
│   ├── core/           # Business logic and data management
│   ├── gui/            # UI components and windows
│   ├── utils/          # Helper utilities
│   └── models/         # Data models
├── main.py             # Entry point
└── config.json         # Global settings (tracks active root)

[Your Root Directory]/
├── jalm_config.json    # Workspace-specific templates (CV/Cover Letter)
├── jalm_apps.db        # Workspace-specific SQLite database
└── [Company Folders]/  # Your application folders
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
JALM uses a two-tier configuration system:
- **Global Config (`config.json`)**: Stored in the app root, it only tracks the `active_root` path.
- **Workspace Config (`jalm_config.json`)**: Stored *inside* each Applications Root folder. It manages CV/Cover Letter template paths specific to that workspace.

### Database Management (`database.py`)
JALM implements **Workspace Isolation**. Each "Applications Root" contains its own `jalm_apps.db`. Switching the root directory in the UI dynamically rebinds the database connection to the new workspace's DB file.

### File Operations (`file_ops.py`)
Contains the logic for:
- Creating hierarchical folder structures (`Root/Company/Role`).
- Cloning and renaming template files using `shutil`.
- Scanning the filesystem for existing `Company/Role` directories to facilitate migration.

### Performance Optimizations
- **Virtual Rendering & Limit**: Shows only the 20 most recent applications by default. The "Show All" toggle enables a chunk-based renderer (`_render_chunk`) that populates the list in small batches (30 items at 20ms intervals) to maintain UI responsiveness.
- **Search Optimization**: Queries are triggered manually via the "Search" button or "Enter" key, reducing unnecessary database load compared to live-filtering.
- **Interactive Headers**: Dynamic sorting with visual indicators (↑/↓) using SQL `ORDER BY` on indexed columns.
- **Throttled Resize**: Window `<Configure>` events are throttled, pausing rendering during active dragging to eliminate lag.

## 🎨 UI Framework

The application is built using `CustomTkinter`, a wrapper around `tkinter` that provides a modern, high-DPI compatible interface.

- **SetupWizard**: A modal window for initial configuration.
- **Dashboard**: The primary interface, utilizing `CTkScrollableFrame` for the application list.
- **ToolTip**: A custom utility in `app/utils` that provides hover-based information for truncated text.

## 🛠️ Error Handling

- **Folder Integrity**: The `AppListItem` checks for the existence of the `folder_path` on every refresh. If the folder is moved or deleted outside JALM, the "Open Folder" button is replaced with a "Path Missing" warning.
- **Database Safety**: Uses SQLite's `ON DELETE CASCADE` to ensure that deleting an application (future feature) would remove related interviews.
