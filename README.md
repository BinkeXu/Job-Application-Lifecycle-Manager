# Job Application Lifecycle Manager (JALM)

JALM is a powerful desktop application designed to streamline and automate your job search process. Built with Python and `CustomTkinter`, it provides a sleek, modern interface for managing applications, automating folder organization, and tracking interview progress.

## 🚀 Features

- **Independent & Portable Workspaces**: Every root folder becomes its own independent workspace. Settings and databases are stored *within* your chosen root, making your job data fully portable.
- **Hybrid Intelligence Service (.NET)**: A high-performance background service that handles heavy lifting like real-time syncing, document automation, and analytics.
- **Real-Time Folder Sync**: Automatically detects when you create, rename, or delete folders in your workspace and syncs them to the database instantly with smart debouncing.
- **Automated Document Generation**: Headlessly clones your CV and Cover Letter templates into new application folders. It automatically updates the date in your Cover Letter (e.g., "10, January 2026").
- **Live Analytics & Export**:
    - **Ghosting Tracking**: Automatically flags applications with no activity for > 30 days.
    - **CSV Export**: Periodically generates a full `applications_export.csv` for use in Excel/Sheets.
    - **Persistent Job Data**: Saves Job Descriptions and Interview Notes as professional `.txt` files directly in each application folder (`job_description.txt` and `interviews.txt`).
    - **Auto-Refresh UI**: The Python dashboard intelligently reloads when it detects background database changes.
- **Advanced Analytics Dashboard**:
    - **Visual Timeline**: Stacked bar charts showing application history (Applied vs. Rejected vs. Offer).
    - **Status Distribution**: Interactive pie charts with hover tooltips.
    - **Detailed Reporting**: Generate a comprehensive **Summary Report** including Success Rate (Interviews / Total), and top Role/Company breakdowns.
    - **Quick Filters**: "Last 7 Days", **"Last 14 Days"**, and "Last 30 Days" shortcuts using a custom Calendar picker.
- **Batch Document Export**:
    - **Selective Backup**: Bulk-export your CVs, JDs, or both for your current search results.
    - **Standardized Renaming**: Automatically renames files for professional organization (e.g., `JobTitle cv 1.pdf`, `JobTitle jd 1.txt`).
    - **Smart Collisions**: Automatically creates timestamped subfolders if exporting to a non-empty directory.
- **Smart Indexing**: Intelligently handles multiple applications to the same company/role by automatically adding sequential indices (e.g., "Software Engineer (2)").
- **High Performance**:
    - **Limit & Toggle**: Shows most recent 20 applications by default for instant loading, with a "Show All" toggle for full history.
    - **Optimized Search**: Filter by company or role using the search bar (supports Enter key).
    - **Database Indexing**: Optimized SQLite queries inside each workspace.
- **Interactive Sorting**: Click on **Company** or **Date** headers to toggle sort order (↑/↓) for quick organization.
- **Sleek UI**:
    - **Visual Status**: Color-coded buttons (Green for Offer, Purple for Interviewing, Red for Rejected).
    - **Context Actions**: Right-click to delete records safely.
    - **Dark-Themed**: Modern CustomTkinter design.

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd "Job Application Lifecycle Manager"
   ```

2. **Install dependencies**:
   ```bash
   pip install customtkinter
   ```

3. **Setup the Background Service (.NET)**:
   - Navigate to `JALM.Service/`
   - Build and run the service:
     ```bash
     dotnet run
     ```
   - (Optional) Build a standalone executable:
     ```bash
     dotnet publish -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true
     ```

4. **Run the Dashboard (Python)**:
   ```bash
   python main.py
   ```

## 📖 Usage

### Initial Setup
On the first run, the **Setup Wizard** will appear. You will need to select:
1. **Your Full Name**: Used for professional naming of CV and Cover Letter templates.
2. **Applications Root Folder**: Where all your job folders will be stored or where they currently exist.
3. **CV Template**: A `.docx` file to be used as a template for new applications.
4. **Cover Letter Template**: A `.docx` file to be used as a template for cover letters.

### Managing Applications
- **Search**: Enter text in the search bar and click **Search** or press **Enter** to filter.
- **Scan & Reload**: Click this to sync your dashboard with your folder structure. It imports new folders and removes "broken" links for folders you've deleted manually.
- **List Limit**: By default, JALM shows the 20 most recent applications. Toggle **Show All** to view your entire history.
- **Sorting**: Click the **Company** or **Date** headers to toggle sort direction.
- **Add Application**: Click `+ Add Application`. JALM automatically appends an index if a duplicate role exists in the same company. You can also paste the **Job Description** here to save it as a text file.
- **Open Folder**: Simply **double-click** any row to jump to that application's local directory. (Red text indicates a missing folder).
- **Interviews**: Click the `Interviews` button to log notes for each round. Notes are saved to the database and appended to an `interviews.txt` file in the folder.
- **Batch Export**: Click **Export Results** to copy all CVs and JDs for your currently filtered list into a single folder. You can choose to export only CVs or only JDs using the popup dialog.
- **Switching Workspaces**: Change your **Applications Root** in Settings to instantly load a different database and template set.
- **Workspace Config (`jalm_config.json`)**: Stored *inside* each Applications Root folder. It manages CV/Cover Letter template paths specific to that workspace.

## 💻 Development & Git Workflow

### Git Commands
To keep your project updated on GitHub:
1. **Check Status**: `git status`
2. **Stage Changes**: `git add .`
3. **Commit**: `git commit -m "Your description of changes"`
4. **Push**: `git push origin main`

### Creating an Executable (.exe)
JALM uses `PyInstaller` to create a standalone Windows executable. 

1. **Install PyInstaller**:
   ```bash
   pip install pyinstaller
   ```

2. **Run Build Command**:
   To ensure all assets and the background service are bundled correctly, allow use the provided spec file:
   ```bash
   pyinstaller JALM.spec --noconfirm
   ```

3. **Locate EXE**: Your standalone executable will be generated in the `dist/` folder as `JALM.exe`.

## 📄 Documentation

For detailed technical information, architecture overview, and database schema, please refer to [DOCUMENTATION.md](DOCUMENTATION.md).

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

## 📜 License

Created as part of a Personal Project.
