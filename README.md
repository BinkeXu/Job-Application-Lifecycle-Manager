# Job Application Lifecycle Manager (JALM)

JALM is a powerful desktop application designed to streamline and automate your job search process. Built with Python and `CustomTkinter`, it provides a sleek, modern interface for managing applications, automating folder organization, and tracking interview progress.

## 🚀 Features

- **Automated Organization**: Automatically creates folders for each application and populates them with standardized CV and Cover Letter templates.
- **Smart Import**: Scans your existing root directory for `Company/Role` structures and imports them automatically into the database.
- **Sequential Interview Tracking**: Log notes and feedback for every round of interviews in a sequence.
- **High Performance**:
    - **Debounced Search**: Smooth, lag-free searching through hundreds of applications.
    - **Database Indexing**: Optimized SQLite queries for instant results.
    - **Batch Rendering**: Fluid UI responsiveness even with large datasets.
- **Visual Integrity**: Detects missing or moved folders and provides visual feedback.
- **Modern UI**: Dark-themed, responsive design with tooltips for long names.

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd "Job Application Manager"
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
1. **Applications Root Folder**: Where all your job folders will be stored or where they currently exist.
2. **CV Template**: A `.docx` file to be used as a template for new applications.
3. **CL Template**: A `.docx` file to be used as a template for cover letters.

### Managing Applications
- **Add Application**: Click the `+ Add Application` button, enter the company and role, and JALM will create the folders and copy your templates.
- **Update Status**: Use the dropdown menu in the list to track your progress (Applied, Interviewing, etc.).
- **Interviews**: Click the `Interviews` button to log notes for each round.
- **Open Folder**: Quickly jump to the application's local directory.

## 📄 Documentation

For detailed technical information, architecture overview, and database schema, please refer to [DOCUMENTATION.md](DOCUMENTATION.md).

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

## 📜 License

Created as part of a Personal Project.
