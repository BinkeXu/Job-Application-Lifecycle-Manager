import customtkinter as ctk
from tkinter import filedialog, messagebox, simpledialog
from ..core.config_mgr import save_config, load_config, get_active_root, set_active_root
from ..core.database import init_db
import os



class AutoScrollableFrame(ctk.CTkScrollableFrame):
    """Custom scrollable frame that properly handles scrollbar visibility."""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        # CTkScrollableFrame handles scrollbar automatically
        # No need for custom logic

class SetupWizard(ctk.CTkToplevel):
    def __init__(self, parent, on_complete_callback):
        super().__init__(parent)
        self.title("JALM - Settings")
        self.geometry("600x700") # Increased size to fit more settings
        self.on_complete_callback = on_complete_callback
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Make it modal
        self.transient(parent)
        self.grab_set()

        self.active_root = get_active_root()
        self.config = load_config()
        self.additional_templates = self.config.get("additional_cv_templates", {}).copy()

        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)  # Row 1 (scroll_frame) expands

        label = ctk.CTkLabel(self, text="JALM Settings & Setup", font=("Arial", 20, "bold"))
        label.grid(row=0, column=0, pady=20, padx=20)
        
        # Scrollable container for all settings
        self.scroll_frame = AutoScrollableFrame(self)
        self.scroll_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 10))
        self.scroll_frame.grid_columnconfigure(0, weight=1)
        
        # Use PACK inside the scroll frame to ensure items stack at the top
        # User Name
        self.user_name_var = ctk.StringVar(value=self.config.get("user_name", ""))
        self.create_name_selector("Your Full Name (for template naming):", self.user_name_var)

        # Root Directory
        self.root_dir_var = ctk.StringVar(value=self.active_root if self.active_root else "")
        self.create_path_selector("Applications Root Folder:", self.root_dir_var, self.select_root_dir)

        # CV Template (Default)
        self.cv_path_var = ctk.StringVar(value=self.config.get("cv_template_path", ""))
        self.create_path_selector("Default CV Template (.docx):", self.cv_path_var, self.select_cv_template)

        # Cover Letter Template
        self.cl_path_var = ctk.StringVar(value=self.config.get("cover_letter_template_path", ""))
        self.create_path_selector("Cover Letter Template (.docx):", self.cl_path_var, self.select_cover_letter_template)

        # Additional CV Templates Section
        self.create_additional_templates_section()

        # Save Button (outside scroll_frame)
        save_btn = ctk.CTkButton(self, text="Save Settings", command=self.save_and_close)
        save_btn.grid(row=2, column=0, pady=20, padx=20)

    def create_path_selector(self, label_text, var, command):
        frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        frame.pack(side="top", fill="x", padx=10, pady=10)
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(frame, text=label_text).grid(row=0, column=0, sticky="w")
        
        entry = ctk.CTkEntry(frame, textvariable=var)
        entry.grid(row=1, column=0, sticky="ew", padx=(0, 10))
        
        btn = ctk.CTkButton(frame, text="Browse", width=80, command=command)
        btn.grid(row=1, column=1)

    def create_name_selector(self, label_text, var):
        frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        frame.pack(side="top", fill="x", padx=10, pady=10)
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(frame, text=label_text).grid(row=0, column=0, sticky="w")
        
        entry = ctk.CTkEntry(frame, textvariable=var, placeholder_text="e.g. John Doe")
        entry.grid(row=1, column=0, sticky="ew", padx=(0, 10))

    def create_additional_templates_section(self):
        frame = ctk.CTkFrame(self.scroll_frame)
        frame.pack(side="top", fill="x", padx=10, pady=20)
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(frame, text="Additional CV Templates", font=("Arial", 14, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        self.templates_list_frame = ctk.CTkFrame(frame, fg_color="transparent")
        self.templates_list_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        self.templates_list_frame.grid_columnconfigure(0, weight=1)
        
        self.refresh_templates_list()
        
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        
        add_btn = ctk.CTkButton(btn_frame, text="+ Add Template", width=120, command=self.add_additional_template)
        add_btn.pack(side="left", padx=5)

    def refresh_templates_list(self):
        # Clear existing
        for widget in self.templates_list_frame.winfo_children():
            widget.destroy()
            
        if not self.additional_templates:
            ctk.CTkLabel(self.templates_list_frame, text="No additional templates added.", text_color="gray").grid(row=0, column=0, pady=5)
            return

        for i, (name, path) in enumerate(self.additional_templates.items()):
            row_frame = ctk.CTkFrame(self.templates_list_frame, fg_color="transparent")
            row_frame.pack(side="top", fill="x", pady=2)
            row_frame.grid_columnconfigure(0, weight=1)
            
            ctk.CTkLabel(row_frame, text=f"• {name}:", font=("Arial", 12, "bold")).pack(side="left", padx=(0, 5))
            
            # Truncate path for display
            display_path = (path[:40] + '...') if len(path) > 40 else path
            ctk.CTkLabel(row_frame, text=display_path, font=("Arial", 10)).pack(side="left")
            
            remove_btn = ctk.CTkButton(row_frame, text="Remove", width=60, height=20, fg_color="#C42B1C", hover_color="#8F1F14",
                                      command=lambda n=name: self.remove_additional_template(n))
            remove_btn.pack(side="right", padx=5)

    def add_additional_template(self):
        name = simpledialog.askstring("Template Name", "Enter a name for this template (e.g. Data Engineer):")
        if not name:
            return
        
        if name in self.additional_templates or name == "Default":
            messagebox.showwarning("Invalid Name", "This template name already exists.")
            return
            
        path = filedialog.askopenfilename(filetypes=[("Word Documents", "*.docx")])
        if path:
            self.additional_templates[name] = path
            self.refresh_templates_list()

    def remove_additional_template(self, name):
        if name in self.additional_templates:
            del self.additional_templates[name]
            self.refresh_templates_list()

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
            if existing_config.get("user_name"):
                self.user_name_var.set(existing_config["user_name"])
            
            # Update additional templates if they exist in the new root's config
            if existing_config.get("additional_cv_templates"):
                self.additional_templates = existing_config["additional_cv_templates"].copy()
                self.refresh_templates_list()

    def select_cv_template(self):
        path = filedialog.askopenfilename(filetypes=[("Word Documents", "*.docx")])
        if path:
            self.cv_path_var.set(path)

    def select_cover_letter_template(self):
        path = filedialog.askopenfilename(filetypes=[("Word Documents", "*.docx")])
        if path:
            self.cl_path_var.set(path)

    def save_and_close(self):
        if not self.user_name_var.get() or not self.root_dir_var.get() or not self.cv_path_var.get() or not self.cl_path_var.get():
            messagebox.showwarning("Incomplete Setup", "Please provide all information to continue.")
            return

        set_active_root(self.root_dir_var.get())
        
        new_config = {
            "user_name": self.user_name_var.get().strip(),
            "cv_template_path": self.cv_path_var.get(),
            "cover_letter_template_path": self.cl_path_var.get(),
            "additional_cv_templates": self.additional_templates
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
                add_application(app['company'], app['role'], app['path'], app.get('created_at'))
                imported_count += 1
        
        if imported_count > 0:
            messagebox.showinfo("Import Complete", f"Found and imported {imported_count} existing applications!")

    def on_closing(self):
        # Only allow closing without setup if config is already complete
        from ..core.config_mgr import is_config_complete
        if is_config_complete():
            self.destroy()
        else:
            if messagebox.askokcancel("Quit", "Setup is required to use JALM. Do you want to quit?"):
                self.master.destroy()
