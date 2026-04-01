# JALM - Local Development Summary & Changelog

This file contains a historical record of major features, bug fixes, and technical solutions implemented since the first version of the Job Application Lifecycle Manager (JALM).

---

## 🌟 New Features

### 1. Independent & Portable Workspaces
- **Issue**: Originally, the app only supported a single hardcoded path, making it difficult to manage different job search profiles or move data.
- **Solution**: Refactored the architecture to support "Applications Roots". Each root contains its own `jalm_config.json` and `jalm_apps.db`.
- **Outcome**: Users can switch workspaces in settings, and data stays localized within the selected folder.

### 2. Scan & Reload (Two-Way Sync)
- **Issue**: Manual changes to the folder structure (e.g., deleting a folder or moving one in) weren't reflected in the database.
- **Solution**: Added a "Scan & Reload" button that:
    1.  **Inbound**: Detects new `Company/Role` folders and imports them.
    2.  **Outbound**: Prunes database records if the physical folder is missing.
- **Outcome**: The database stays in perfect sync with the filesystem.

### 3. Smart Indexing for Duplicate Roles
- **Issue**: Applying to the same role at the same company caused folder path conflicts.
- **Solution**: Implemented a check during the "Add Application" process. If a duplicate exists, it offers to append a sequential index (e.g., `Software Engineer (2)`).
- **Outcome**: Prevents data over-writes and allows tracking multiple attempts at the same role.

### 4. Dynamic Template Naming
- **Issue**: Files were originally named generically (e.g., `CL.docx`), which wasn't professional for submissions.
- **Solution**: 
    - Formatted as `[User Name]_CV_[Role].docx`.
    - Added a **User Name** field in setup to allow fully dynamic naming.
- **Outcome**: Files are ready for instant upload/email.

### 5. UI/UX Improvements
- **Action Simplification**: Removed dedicated "Open Folder" buttons in favor of **Double-Click** on rows.
- **Search Enhancements**: Bound the **Enter Key** to search and form submission for faster workflow.
- **Visual Feedback**: Missing folders now turn the text **Red** in the dashboard list.

### 6. Filesystem-to-Date Synchronization
- **Issue**: Importing existing folders or reloading the workspace set the "Applied Date" to the current time, losing historical data.
- **Solution**: Updated `file_ops.py` to fetch the metadata birth time (Creation Time) from the folder. Updated `database.py` to accept specific timestamps.
- **Outcome**: The "Date Applied" now accurately reflects when the application folder was created on Windows.

### 7. Multiple CV Templates
- **Issue**: Users often have different versions of their CV for different roles (e.g., Generalist vs. Specialist), but the app only supported one global CV template.
- **Solution**: 
    1.  **Settings**: Added an "Additional CV Templates" manager in the Setup Wizard.
    2.  **Add Dialog**: Integrated a dropdown menu to select which CV to use during application creation.
- **Outcome**: Allows for high-precision role targeting with zero manual file copying.

### 8. Granular Application Statuses & Semantic Sorting
- **Issue**: The application pipeline lacked pre-interview granularity (like Online Assessments and HR calls), and attempting to sort the dashboard by "Status" resulted in a chaotic alphabetical order (Applied -> Ghosted -> HR Call -> Interviewed -> OA -> Offer -> Rejected) which destroyed the timeline.
- **Solution**: 
    1.  **Pipeline Expansion**: Added "OA" (Online Assessment) and "HR Call" tracking states to the dashboard, complete with distinct color coding across the UI and analytics charts. Updated the global success metric to actively register these benchmarks.
    2.  **Semantic SQL Sorting**: Implemented an internal SQLite `ORDER BY CASE` mapping that translates text statuses into ordinal numerical values, forcing a logical chronological sort: `Applied -> OA -> HR Call -> Interviewed -> Offer -> Rejected -> Ghosted`.
- **Outcome**: A detailed tracking pipeline that stays visually organized and chronologically coherent when sorted.

### 9. Analytics YTD Defaults & Calendar Fast Navigation
- **Issue**: The Analytics Dashboard always loaded "All Time" data by default, requiring tedious manual calendar clicking to filter. The Calendar popup itself lacked fast year-jumping mechanics, and its hardcoded colors broke under dark mode.
- **Solution**: 
    1.  **YTD Automation**: The dashboard now calculates and pre-fills the Year-To-Date range on launch, and features a one-click `YTD` quick-access filter.
    2.  **Calendar Upgrades**: Added `<<` and `>>` fast-travel year buttons to the calendar widget, and dynamically bound text colors to the native theme engine to ensure perfect contrast in both Light and Dark themes.
- **Outcome**: A fluid, responsive date-filtering experience tailored for modern UI themes.

### 10. AI-Powered Role Categorization
- **Issue**: Analytics reports grouped highly similar titles (e.g., "Junior Web Dev", "Front End Developer", "SWE") as separate lines, creating fragmented and unreadable charts.
- **Solution**: 
    1.  **Local LLM Integration**: Implemented a background integration with Ollama (defaulting to `llama3.2`) to zero-shot classify job titles into a strict predefined list of standardized industry categories.
    2.  **Database Caching**: Added a `role_mappings` table to permanently cache LLM classifications, ensuring lightning-fast subsequent loads and zero redundant API calls.
    3.  **Role Classification Manager**: Built a completely interactive UI (`RoleMappingDialog`) that allows users to review the AI's automated decisions, apply manual overrides, configure the LLM model name, and force bulk re-classifications by clearing the cache.
- **Outcome**: Analytics reports are now perfectly grouped by broad professional categories with no manual data entry required.

---

## 🐛 Bug Fixes & Technical Solutions

### 10. Code architecture and Stability Update (2026-04-01)
- **Issue**: A code review identified UI freezing during LLM requests, possible SQLite database connection leaks on exceptions, silent failures in config loading, and DRY pattern violations with role categories.
- **Solution**:
    1.  **Asynchronous Analytics**: Refactored the `open_summary_report` to run LLM invocations in a background `threading.Thread`, preventing `customtkinter` UI freezes and adding an interactive loading modal.
    2.  **Robust Error Handling**: Wrapped all SQLite queries across `database.py` in `try...finally: conn.close()` to guarantee safe file closures and connection cleanup.
    3.  **DRY Refactoring**: Centralized AI job role lists into a single `constants.py` file, simplifying future category additions.
    4.  **Diagnostics**: Added exception printing to `config_mgr.py` to trace corrupted configs.
- **Outcome**: A significantly more stable, responsive, and DRY application architecture.

### 1. Performance: Scroll Lag with Large Lists
- **Issue**: Creating hundreds of Tkinter widgets simultaneously frozen the UI.
- **Solution**: 
    1.  **Batch Rendering**: Implemented a recursive chunk renderer (`_render_chunk`) that populates the list in small batches.
    2.  **Listing Limits**: Default view now shows only the 20 most recent items, with a "Show All" toggle for older records.
- **Outcome**: Smooth, instant loading even with 100+ applications.

### 2. GUI Artifacts on Resize
- **Issue**: Rapidly resizing the window caused widget overlap and flickering.
- **Solution**: Implemented **Resize Throttling**. The rendering engine pauses during active resize events and only resumes after a short delay (debouncing).
- **Outcome**: Stable and predictable UI layout.

### 3. Config Migration Issues
- **Issue**: Renaming keys (like `cl_template_path` to `cover_letter_template_path`) broke old setups.
- **Solution**: Added logic in `config_mgr.py` to check for legacy keys and automatically move values to new keys upon loading.
- **Outcome**: Transparent upgrades for existing users.

### 4. Database Concurrency/Pathing
- **Issue**: Using a relative path for `applications.db` caused issues when running the exe from different locations.
- **Solution**: Changed database connection logic to use **Absolute Paths** derived from the `active_root` setting.
- **Outcome**: Rock-solid stability regardless of where the app is launched.

### 5. Settings Layout & Spacing
- **Issue**: The Settings page had large empty gaps and an awkwardly positioned scrollbar that appeared even when not needed.
- **Solution**: 
    1.  **Pack Layout**: Switched internal settings widgets from Grid to Pack to eliminate blank spacing at the top.
    2.  **Auto-Scrollbar**: Implemented a simplified scrollbar behavior that only appears on the right side when content overflows.
    3.  **Expansion Logic**: Updated grid weights to ensure the settings area stretches to fill the window.
- **Outcome**: A clean, professional settings interface that feels native and responsive.

### 6. Robust Scan & Reload (Data Loss Fix)
- **Issue**: Renaming an application folder on the filesystem caused the sync logic to treat it as a new application and delete the old record, resulting in the quiet deletion of all associated interview notes (due to cascading wipes).
- **Solution**: 
    1.  **Hidden Identifiers**: The app now generates a hidden `.jalm_id` file inside each application folder to permanently link it to a database record.
    2.  **Centralized Sync Hub**: Refactored the UI layers to use a shared `sync_mgr.py` service that matches ids securely, preventing ghost deletions and safely updating renamed routes.
    3.  **Setup Wizard Parity**: Fixed a bug where importing old workspaces in the Setup Wizard ignored the `has_interviews` flag by plugging it into the new central sync service.
- **Outcome**: The database will no longer randomly drop interview records if a user decides to format or rename their job application folders.

### 7. Analytics & Reporting (Performance & Accuracy)
- **Issue**: Hovering over charts caused severe UI flickering and CPU spikes. Additionally, the "Success Rate" was mathematically incorrect as it dropped applications that transitioned to "Offer" or "Rejected" without notes, and the timeline chart skipped empty days, distorting the visual sense of time.
- **Solution**: 
    1.  **State-Aware Interaction**: Optimized `analytics_view.py` to only redraw tooltips when the mouse enters a new data element, eliminating the per-pixel canvas reload.
    2.  **Conversion Logic Fix**: Updated `database.py` to correctly track interview history for successful applications, ensuring "Offer" status contributes to the interview tally.
    3.  **Continuous Time Axis**: Implemented a "Date Padding" algorithm in the timeline renderer to ensure every day in a range is visible, even if zero applications were submitted.
    4.  **Report UI Polish**: Improved table formatting in `report_dialog.py` with descriptive headers and right-aligned numerical data.
- **Outcome**: A professional, smooth, and statistically accurate analytics dashboard.

### 8. Full-Stack Architecture & Security Audit (2026-03-20)
- **Issue**: A comprehensive audit identified 20+ vulnerabilities, logic bugs, and scalability bottlenecks, including a critical "false success" error handler, SQL injection risks, and N+1 query patterns.
- **Solution**:
    1.  **Logic & Security**: 
        - Fixed a duplicated `except` block that masked creation failures as "Success".
        - Implemented **SQL Injection Defense** via whitelist validation for sort parameters.
        - Enabled **Global Foreign Keys** to guarantee data integrity and cascade deletes.
        - Resolved a **File Handle Leak** in the background service manager.
        - Refactored `set_active_root` to preserve existing configuration keys (Read-Modify-Write).
        - Replaced non-atomic interview sequencing with **Atomic SQL Transactions** to prevent race conditions.
    2.  **Usability & UI Polish**:
        - Implemented **Live Search Debounce** (300ms) for real-time filtering.
        - Added a **Truncation Notice** ("Showing 20 of N") for visual transparency.
        - Made the **Role column sortable** with interactive header arrows.
        - Enhanced the Calendar with **Selection Highlighting** for better context.
        - Fixed a crash related to `sqlite3.Row` null-safe date access.
    3.  **Scalability**:
        - Eliminated the **N+1 Query Pattern** in workspace synchronization, resulting in significantly faster reloads for large application lists.
        - Optimized `config_mgr.py` to resolve paths relative to the executable for portable stability.
        - Implemented cross-platform support for `open_folder` (Windows/macOS/Linux).
- **Outcome**: A production-hardened, secure, and highly scalable application architecture ready for large-scale deployment.

### 9. Refined Success Metrics & Funnel Reporting (2026-03-21)
- **Issue**: The "Success Rate" was originally calculated as a simple `Interviews / Total Apps` conversion, which didn't account for how effectively an applicant performs *during* an interview. Additionally, pre-interview stages like Online Assessments (OA) and HR Calls were lumped together, making it hard to identify exactly where the "bottleneck" was in the application funnel.
- **Solution**:
    1.  **Funnel Segmentation**: Introduced dedicated tracking and reporting for **OA** and **HR Call** roles. These stages now appear as distinct groups in the summary report, complete with dedicated role lists.
    2.  **Success Rate 2.0**: Redefined the global Success Rate to reflect **Interview-to-Offer conversion**. It now only considers applications that reached the interview status, providing a professional metric of interview performance.
    3.  **UI Scalability**: Upgraded the master application window to `1300x800` and the Analytics Report to `1100x800` with a two-tier metrics layout. This prevents text squashing and button clipping when viewing dense datasets.
    4.  **Uniform Reporting**: Standardized all report roles tables (Interviewed, OA, HR Call) to use a consistent `Name | Count` format for professional readability.
- **Outcome**: A high-fidelity, professional analytics experience that provides clear insights into every stage of the job search funnel.

---

## 🛠️ Build & Distribution
- **Executable**: Successfully bundled into a single-file EXE using `PyInstaller`.
- **CustomTkinter Assets**: Solved the "missing theme" bug by manually adding the `customtkinter` site-packages directory to the build data (`--add-data`).
- **Standardized Binaries**: The .NET Background Service is now correctly bundled within the `dist/JALM.exe` package.
