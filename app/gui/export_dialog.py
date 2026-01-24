import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
from ..core.batch_export import BatchExporter

class ExportDialog(ctk.CTkToplevel):
    """
    A modal dialog that allows users to configure and initiate a batch export.
    Features include selecting document types (CV/JD) and choosing a destination folder.
    """
    def __init__(self, parent, app_list, search_query=""):
        super().__init__(parent)
        self.title("Export Options")
        self.geometry("400x350")
        self.resizable(False, False)
        
        self.app_list = app_list
        self.search_query = search_query
        self.parent = parent
        
        # UI Polish: Center the dialog relative to the main application window.
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (400 // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (350 // 2)
        self.geometry(f"+{x}+{y}")
        
        self.grab_set() # Prevent interaction with parent while open
        self.setup_ui()
        
    def setup_ui(self):
        """Builds the dialog interface with checkboxes and folder selection."""
        # Header Section
        ctk.CTkLabel(self, text="Export Applications", font=("Arial", 18, "bold")).pack(pady=20)
        ctk.CTkLabel(self, text=f"Ready to export {len(self.app_list)} records.", text_color="gray").pack(pady=(0, 20))
        
        # Options Frame: Select what to export
        self.opts_frame = ctk.CTkFrame(self)
        self.opts_frame.pack(fill="x", padx=20, pady=10)
        
        self.cv_var = ctk.BooleanVar(value=True)
        self.jd_var = ctk.BooleanVar(value=True)
        
        self.cv_chk = ctk.CTkCheckBox(self.opts_frame, text="Export CVs", variable=self.cv_var)
        self.cv_chk.pack(pady=(10, 5), padx=20, anchor="w")
        
        self.jd_chk = ctk.CTkCheckBox(self.opts_frame, text="Export Job Descriptions", variable=self.jd_var)
        self.jd_chk.pack(pady=(5, 20), padx=20, anchor="w")
        
        # Target Directory Selection: Show current selection and a Browse button
        self.dir_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.dir_frame.pack(fill="x", padx=20, pady=10)
        
        self.path_var = ctk.StringVar(value="")
        self.path_entry = ctk.CTkEntry(self.dir_frame, textvariable=self.path_var, placeholder_text="No folder selected", state="disabled")
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.browse_btn = ctk.CTkButton(self.dir_frame, text="Browse", width=80, command=self.on_browse)
        self.browse_btn.pack(side="right")
        
        # Action Buttons (Cancel / Start Export)
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(side="bottom", fill="x", padx=20, pady=20)
        
        self.cancel_btn = ctk.CTkButton(self.btn_frame, text="Cancel", fg_color="gray", hover_color="#555555", command=self.destroy)
        self.cancel_btn.pack(side="left", expand=True, padx=5)
        
        self.export_btn = ctk.CTkButton(self.btn_frame, text="Start Export", command=self.on_export)
        self.export_btn.pack(side="right", expand=True, padx=5)

    def on_browse(self):
        """Opens a standard directory picker."""
        directory = filedialog.askdirectory(parent=self, title="Select Destination")
        if directory:
            self.path_var.set(directory)

    def on_export(self):
        """Validates inputs and triggers the BatchExporter core logic."""
        target_dir = self.path_var.get()
        if not target_dir:
            messagebox.showwarning("Validation Error", "Please select a destination folder.", parent=self)
            return
            
        if not self.cv_var.get() and not self.jd_var.get():
            messagebox.showwarning("Validation Error", "Please select at least one document type to export.", parent=self)
            return

        # Visual Feedback: Disable buttons to prevent double-clicks during file IO
        self.export_btn.configure(state="disabled", text="Exporting...")
        self.browse_btn.configure(state="disabled")
        self.update()
        
        try:
            # Execute the background export process
            exporter = BatchExporter()
            stats = exporter.export(
                self.app_list, 
                target_dir, 
                search_query=self.search_query,
                export_cv=self.cv_var.get(),
                export_jd=self.jd_var.get()
            )
            
            # Show final report to user
            msg = "Export Complete!\n\n"
            if self.cv_var.get():
                msg += f"CVs exported: {stats['exported_cvs']}\n"
            if self.jd_var.get():
                msg += f"JDs exported: {stats['exported_jds']}\n"
                
            if stats['errors']:
                msg += f"\nErrors ({len(stats['errors'])}):\n" + "\n".join(stats['errors'][:3])
                if len(stats['errors']) > 3:
                    msg += "\n..."
            
            messagebox.showinfo("Success", msg, parent=self.parent)
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Export Failed", f"An error occurred: {e}", parent=self)
            self.export_btn.configure(state="normal", text="Start Export")
            self.browse_btn.configure(state="normal")
