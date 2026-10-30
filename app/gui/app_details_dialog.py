import os
import customtkinter as ctk
from tkinter import messagebox, Menu
from ..core.database import get_application_by_id, update_application_status, update_application_job_description, get_interviews
from ..core.file_ops import open_folder, save_job_description_file

class AppDetailsDialog(ctk.CTkToplevel):
    """
    A comprehensive modal dialog for viewing and updating an application's details,
    including reading and editing the Job Description, updating its status,
    opening its workspace folder, and viewing associated interview logs.
    """
    def __init__(self, parent, app_id, on_refresh_callback=None):
        super().__init__(parent)
        self.parent = parent
        self.app_id = app_id
        self.on_refresh_callback = on_refresh_callback

        # Fetch fresh data from DB
        raw_data = get_application_by_id(self.app_id)
        if not raw_data:
            messagebox.showerror("Error", "Application record not found.", parent=parent)
            self.destroy()
            return

        self.app_data = dict(raw_data)
        self.company = self.app_data.get('company_name', '')
        self.role = self.app_data.get('role_name', '')
        self.folder_path = self.app_data.get('folder_path') or ""
        self.current_status = self.app_data.get('status') or "Applied"
        self.created_at = self.app_data.get('created_at') or "N/A"

        self.title(f"Application Details - {self.company} ({self.role})")
        self.geometry("700x700")
        self.minsize(600, 500)

        # Center modal relative to parent
        self.update_idletasks()
        try:
            x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (700 // 2)
            y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (700 // 2)
            self.geometry(f"+{max(0, x)}+{max(0, y)}")
        except Exception:
            pass

        self.transient(parent)
        self.grab_set()

        self.setup_ui()
        self.load_job_description()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # 1. Header Frame (Company, Role, Status)
        header_frame = ctk.CTkFrame(self)
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 10))
        header_frame.grid_columnconfigure(0, weight=1)

        # Title and Role
        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(fill="x", padx=15, pady=(10, 5))
        
        comp_label = ctk.CTkLabel(title_box, text=self.company, font=("Arial", 20, "bold"), anchor="w")
        comp_label.pack(side="left")
        
        role_label = ctk.CTkLabel(title_box, text=f"—  {self.role}", font=("Arial", 16), text_color="gray", anchor="w")
        role_label.pack(side="left", padx=10)

        # Sub-header: Status & Date
        meta_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        meta_box.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkLabel(meta_box, text="Status:", font=("Arial", 12, "bold")).pack(side="left")
        
        self.status_var = ctk.StringVar(value=self.current_status)
        self.status_menu = ctk.CTkOptionMenu(
            meta_box,
            values=["Applied", "OA", "HR Call", "Interviewed", "Offer", "Rejected", "Ghosted"],
            variable=self.status_var,
            command=self.on_status_change,
            width=130
        )
        self.status_menu.pack(side="left", padx=(8, 20))
        self._update_status_color(self.current_status)

        # Date Display
        date_str = self.created_at.split(' ')[0] if self.created_at else 'N/A'
        ctk.CTkLabel(meta_box, text=f"Applied Date: {date_str}", font=("Arial", 12), text_color="gray").pack(side="left")

        # 2. Folder Location Bar
        folder_frame = ctk.CTkFrame(self)
        folder_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))

        exists = os.path.exists(self.folder_path) if self.folder_path else False
        folder_text = self.folder_path if self.folder_path else "No folder assigned"
        folder_color = ("black", "white") if exists else "#EF4444"

        ctk.CTkLabel(folder_frame, text="Folder:", font=("Arial", 12, "bold")).pack(side="left", padx=(15, 5), pady=8)
        self.folder_label = ctk.CTkLabel(folder_frame, text=folder_text, font=("Arial", 11), text_color=folder_color, anchor="w")
        self.folder_label.pack(side="left", fill="x", expand=True, padx=5, pady=8)

        self.btn_open_folder = ctk.CTkButton(
            folder_frame, 
            text="📁 Open Folder", 
            width=110, 
            height=28,
            command=self.on_open_folder
        )
        self.btn_open_folder.pack(side="right", padx=10, pady=8)

        # 3. Job Description Editor Area
        jd_frame = ctk.CTkFrame(self)
        jd_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 10))
        jd_frame.grid_columnconfigure(0, weight=1)
        jd_frame.grid_rowconfigure(1, weight=1)

        jd_toolbar = ctk.CTkFrame(jd_frame, fg_color="transparent")
        jd_toolbar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))

        ctk.CTkLabel(jd_toolbar, text="Job Description", font=("Arial", 14, "bold")).pack(side="left")

        self.btn_save_jd = ctk.CTkButton(
            jd_toolbar, 
            text="💾 Save JD Changes", 
            width=130, 
            height=28,
            fg_color="#10B981", 
            hover_color="#059669", 
            command=self.on_save_jd
        )
        self.btn_save_jd.pack(side="right", padx=(5, 0))

        self.btn_copy_jd = ctk.CTkButton(
            jd_toolbar, 
            text="📋 Copy JD", 
            width=90, 
            height=28,
            fg_color="#4B5563", 
            hover_color="#374151", 
            command=self.on_copy_jd
        )
        self.btn_copy_jd.pack(side="right")

        self.jd_textbox = ctk.CTkTextbox(jd_frame, wrap="word", font=("Arial", 12))
        self.jd_textbox.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.setup_textbox_context_menu(self.jd_textbox)

        # 4. Footer Actions
        footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        footer_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 15))

        # Interview shortcut
        interviews = get_interviews(self.app_id)
        interview_count = len(interviews) if interviews else 0
        btn_text = f"🎤 View / Log Interviews ({interview_count})"
        self.btn_interviews = ctk.CTkButton(
            footer_frame,
            text=btn_text,
            width=200,
            fg_color="#8B5CF6",
            hover_color="#7C3AED",
            command=self.on_open_interviews
        )
        self.btn_interviews.pack(side="left")

        self.btn_close = ctk.CTkButton(
            footer_frame,
            text="Close",
            width=100,
            fg_color="gray",
            hover_color="#4B4B4B",
            command=self.destroy
        )
        self.btn_close.pack(side="right")

    def load_job_description(self):
        """Loads JD text from database or falls back to job_description.txt file on disk."""
        jd_text = self.app_data.get('job_description') or ""
        
        # Fallback check on disk if DB record is empty
        if not jd_text and self.folder_path and os.path.exists(self.folder_path):
            jd_file = os.path.join(self.folder_path, "job_description.txt")
            if os.path.exists(jd_file):
                try:
                    with open(jd_file, "r", encoding="utf-8") as f:
                        jd_text = f.read()
                except Exception as e:
                    print(f"Failed to read job_description.txt fallback: {e}")

        self.jd_textbox.delete("1.0", "end")
        if jd_text:
            self.jd_textbox.insert("1.0", jd_text)

    def on_status_change(self, new_status):
        """Updates the status in the database and triggers parent refresh."""
        self.current_status = new_status
        update_application_status(self.app_id, new_status)
        self._update_status_color(new_status)
        if self.on_refresh_callback:
            self.on_refresh_callback()

    def _update_status_color(self, status):
        """Color-codes the status dropdown to match dashboard theme."""
        if status == "Rejected":
            color, hover = "#C42B1C", "#8F1F14"
        elif status == "Ghosted":
            color, hover = "#D97706", "#B45309"
        elif status == "Offer":
            color, hover = "#10B981", "#059669"
        elif status == "OA":
            color, hover = "#0891B2", "#0E7490"
        elif status == "HR Call":
            color, hover = "#DB2777", "#BE185D"
        elif status == "Interviewed":
            color, hover = "#8B5CF6", "#7C3AED"
        else:
            color = ["#3B8ED0", "#1F6AA5"]
            hover = ["#36719F", "#27577D"]
        self.status_menu.configure(fg_color=color, button_color=color, button_hover_color=hover)

    def on_save_jd(self):
        """Saves current textbox contents to both DB and job_description.txt."""
        content = self.jd_textbox.get("1.0", "end-1c").strip()
        try:
            update_application_job_description(self.app_id, content)
            if self.folder_path and os.path.exists(self.folder_path):
                save_job_description_file(self.folder_path, content)
            messagebox.showinfo("Saved", "Job description updated successfully!", parent=self)
            if self.on_refresh_callback:
                self.on_refresh_callback()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save job description: {e}", parent=self)

    def on_copy_jd(self):
        """Copies JD to clipboard."""
        content = self.jd_textbox.get("1.0", "end-1c")
        if not content.strip():
            messagebox.showinfo("Notice", "Job description is empty.", parent=self)
            return
        self.clipboard_clear()
        self.clipboard_append(content)
        messagebox.showinfo("Copied", "Job description copied to clipboard!", parent=self)

    def on_open_folder(self):
        if not self.folder_path or not os.path.exists(self.folder_path):
            messagebox.showerror("Missing Folder", f"Folder does not exist:\n{self.folder_path}", parent=self)
            return
        try:
            open_folder(self.folder_path)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder: {e}", parent=self)

    def on_open_interviews(self):
        from .interview_manager import InterviewManager
        InterviewManager(self, self.app_id, self.company, self.role)
        # Update interview count on modal after closing interviews
        interviews = get_interviews(self.app_id)
        self.btn_interviews.configure(text=f"🎤 View / Log Interviews ({len(interviews)})")

    def setup_textbox_context_menu(self, textbox):
        """Attaches standard Cut/Copy/Paste/Select-All context menu to the textbox."""
        menu = Menu(textbox, tearoff=0)
        menu.add_command(label="Cut", command=lambda: textbox.event_generate("<<Cut>>"))
        menu.add_command(label="Copy", command=lambda: textbox.event_generate("<<Copy>>"))
        menu.add_command(label="Paste", command=lambda: textbox.event_generate("<<Paste>>"))
        menu.add_separator()
        menu.add_command(label="Select All", command=lambda: textbox.tag_add("sel", "1.0", "end"))

        def show_menu(event):
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()

        target_widget = getattr(textbox, "_textbox", textbox)
        target_widget.bind("<Button-3>", show_menu)
        textbox.bind("<Button-3>", show_menu)
