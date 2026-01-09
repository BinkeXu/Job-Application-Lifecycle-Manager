# Job Application Lifecycle Manager (JALM)

JALM is a powerful desktop application designed to streamline and automate your job search process. Built with Python and `CustomTkinter`, it provides a sleek, modern interface for managing applications, automating folder organization, and tracking interview progress.

## 🚀 Features

- **Independent & Portable Workspaces**: Every root folder becomes its own independent workspace. Settings and databases are stored *within* your chosen root, making your job data fully portable.
    ```
    ├── [Your Root Directory]/
    │   ├── jalm_config.json    # Workspace-specific templates (CV/Cover Letter)
    │   ├── jalm_apps.db        # Workspace-specific SQLite database
    │   └── [Company Folders]/  # Your application folders
    ```
- **Automated Organization**: Automatically creates folders for each application and populates them with standardized CV and Cover Letter templates using a professional format: `[Your Name]_CV_[Role Name].docx`.
- **Scan & Reload (Two-Way Sync)**: Synchronizes your database with your local files. It automatically imports new folders found on disk, synchronizes application dates with folder creation dates, and cleans up database entries for folders that have been moved or deleted.
- **Smart Indexing**: Intelligently handles multiple applications to the same company/role by automatically adding sequential indices (e.g., "Software Engineer (2)").
- **High Performance**:
    - **Limit & Toggle**: Shows most recent 20 applications by default for instant loading, with a "Show All" toggle for full history.
    - **Optimized Search**: Filter by company or role using the search bar (supports Enter key).
    - **Database Indexing**: Optimized SQLite queries inside each workspace.
- **Interactive Sorting**: Click on **Company** or **Date** headers to toggle sort order (↑/↓) for quick organization.
- **Sleek UI**: Dark-themed design with double-click to open folders and red-text warnings for missing paths.

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

3. **Run the application**:
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
- **Add Application**: Click `+ Add Application`. JALM automatically appends an index if a duplicate role exists in the same company.
- **Open Folder**: Simply **double-click** any row to jump to that application's local directory. (Red text indicates a missing folder).
- **Interviews**: Click the `Interviews` button to log notes for each round.
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
   Use the following command to bundle the app with its high-DPI assets:
   ```bash
   pyinstaller --noconsole --onefile --add-data "C:\Python38\lib\site-packages\customtkinter;customtkinter/" --name "Job Application Lifecycle Manager" main.py
   ```
   *(Note: Ensure the path to `customtkinter` matches your Python installation site-packages.)*

3. **Locate EXE**: Your standalone executable will be generated in the `dist/` folder.

## 📄 Documentation

For detailed technical information, architecture overview, and database schema, please refer to [DOCUMENTATION.md](DOCUMENTATION.md).

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

## 📜 License

Created as part of a Personal Project.
