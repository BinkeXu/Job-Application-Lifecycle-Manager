import customtkinter as ctk
from tkinter import filedialog, messagebox
from ..core.config_mgr import save_config, load_config, get_active_root, set_active_root
from ..core.database import init_db
import os

class SetupWizard(ctk.CTkToplevel):
    def __init__(self, parent, on_complete_callback):
        super().__init__(parent)
        self.title("JALM - Initial Setup")
        self.geometry("500x400")
        self.on_complete_callback = on_complete_callback
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Make it modal
        self.transient(parent)
        self.grab_set()

        self.active_root = get_active_root()
        self.config = load_config()

        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)

        label = ctk.CTkLabel(self, text="Job Application Lifecycle Manager Setup", font=("Arial", 20, "bold"))
        label.grid(row=0, column=0, pady=20, padx=20)

        # Root Directory
        self.root_dir_var = ctk.StringVar(value=self.active_root if self.active_root else "")
        self.create_path_selector(1, "Applications Root Folder:", self.root_dir_var, self.select_root_dir)

        # CV Template
        self.cv_path_var = ctk.StringVar(value=self.config.get("cv_template_path", ""))
        self.create_path_selector(2, "CV Template (.docx):", self.cv_path_var, self.select_cv_template)

        # Cover Letter Template
        self.cl_path_var = ctk.StringVar(value=self.config.get("cover_letter_template_path", ""))
        self.create_path_selector(3, "Cover Letter Template (.docx):", self.cl_path_var, self.select_cover_letter_template)

        # Save Button
        save_btn = ctk.CTkButton(self, text="Complete Setup", command=self.save_and_close)
        save_btn.grid(row=4, column=0, pady=30, padx=20)

    def create_path_selector(self, row, label_text, var, command):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=row, column=0, sticky="ew", padx=20, pady=10)
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(frame, text=label_text).grid(row=0, column=0, sticky="w")
        
        entry = ctk.CTkEntry(frame, textvariable=var)
        entry.grid(row=1, column=0, sticky="ew", padx=(0, 10))
        
        btn = ctk.CTkButton(frame, text="Browse", width=80, command=command)
        btn.grid(row=1, column=1)

    def select_root_dir(self):
        path = filedialog.askdirectory()
        if path:
            self.root_dir_var.set(path)
            # Temporarily set active root to try and load existing config from there
            old_root = get_active_root()
            set_active_root(path)
            existing_config = load_config()
            
            if existing_config.get("cv_template_path"):
                self.cv_path_var.set(existing_config["cv_template_path"])
            if existing_config.get("cover_letter_template_path"):
                self.cl_path_var.set(existing_config["cover_letter_template_path"])
            
            # Revert if not saving yet? No, actually it's fine to leave it pointed there
            # as it will be finalized in save_and_close

    def select_cv_template(self):
        path = filedialog.askopenfilename(filetypes=[("Word Documents", "*.docx")])
        if path:
            self.cv_path_var.set(path)

    def select_cover_letter_template(self):
        path = filedialog.askopenfilename(filetypes=[("Word Documents", "*.docx")])
        if path:
            self.cl_path_var.set(path)

    def save_and_close(self):
        if not self.root_dir_var.get() or not self.cv_path_var.get() or not self.cl_path_var.get():
            messagebox.showwarning("Incomplete Setup", "Please provide all paths to continue.")
            return

        set_active_root(self.root_dir_var.get())
        
        new_config = {
            "cv_template_path": self.cv_path_var.get(),
            "cover_letter_template_path": self.cl_path_var.get()
        }
        save_config(new_config)
        
        # Initialize the database in the new root
        init_db()
        
        # Import existing applications
        self.import_existing_folders(self.root_dir_var.get())
        
        self.on_complete_callback()
        self.destroy()

    def import_existing_folders(self, root_path):
        from ..core.file_ops import scan_for_existing_applications
        from ..core.database import add_application, application_exists
        
        found_apps = scan_for_existing_applications(root_path)
        imported_count = 0
        
        for app in found_apps:
            if not application_exists(app['company'], app['role']):
                add_application(app['company'], app['role'], app['path'])
                imported_count += 1
        
        if imported_count > 0:
            messagebox.showinfo("Import Complete", f"Found and imported {imported_count} existing applications!")

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Setup is required to use JALM. Do you want to quit?"):
            self.master.destroy()
