import customtkinter as ctk
import os
from .add_app_dialog import AddAppDialog
from ..core.database import add_application, get_applications, get_stats, update_application_status
from ..core.file_ops import create_application_folder, open_folder
from ..utils.tooltip import ToolTip
from tkinter import messagebox

class StatsCard(ctk.CTkFrame):
    def __init__(self, parent, title, value):
        super().__init__(parent)
        
        self.title_label = ctk.CTkLabel(self, text=title, font=("Arial", 14))
        self.title_label.pack(pady=(10, 0), padx=20)
        
        self.value_label = ctk.CTkLabel(self, text=str(value), font=("Arial", 24, "bold"))
        self.value_label.pack(pady=(0, 10), padx=20)

    def update_value(self, new_value):
        self.value_label.configure(text=str(new_value))

class AppListItem(ctk.CTkFrame):
    def __init__(self, parent, app_data, on_refresh):
        super().__init__(parent)
        self.app_data = app_data
        self.on_refresh = on_refresh
        
        self.setup_ui()

    def setup_ui(self):
        # Truncate text for display
        display_company = self.app_data['company_name']
        if len(display_company) > 25:
            display_company = display_company[:22] + "..."
            
        display_role = self.app_data['role_name']
        if len(display_role) > 25:
            display_role = display_role[:22] + "..."

        # Data columns
        company_label = ctk.CTkLabel(self, text=display_company, width=200, anchor="w")
        company_label.pack(side="left", padx=10)
        ToolTip(company_label, self.app_data['company_name'])
        
        role_label = ctk.CTkLabel(self, text=display_role, width=200, anchor="w")
        role_label.pack(side="left", padx=10)
        ToolTip(role_label, self.app_data['role_name'])
        
        # Status dropdown
        self.status_var = ctk.StringVar(value=self.app_data['status'])
        self.status_menu = ctk.CTkOptionMenu(self, 
                                           values=["Applied", "Interviewing", "Rejected", "Offer", "Ghosted"],
                                           variable=self.status_var,
                                           command=self.on_status_change,
                                           width=120)
        self.status_menu.pack(side="left", padx=10)
        
        date_str = self.app_data['created_at'].split(' ')[0] # Just date part
        ctk.CTkLabel(self, text=date_str, width=120, anchor="w").pack(side="left", padx=10)

        # Actions
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(side="right", padx=10)
        
        self.open_btn = ctk.CTkButton(btn_frame, text="Open Folder", width=100, command=self.on_open_folder)
        self.open_btn.pack(side="right", padx=5)

        self.interview_btn = ctk.CTkButton(btn_frame, text="Interviews", width=100, command=self.on_open_interviews)
        self.interview_btn.pack(side="right", padx=5)

        # Folder check
        if not os.path.exists(self.app_data['folder_path']):
            self.open_btn.configure(state="disabled", text="Path Missing", fg_color="red")

    def on_status_change(self, new_status):
        update_application_status(self.app_data['id'], new_status)
        self.on_refresh()

    def on_open_folder(self):
        try:
            open_folder(self.app_data['folder_path'])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder: {e}")

    def on_open_interviews(self):
        from .interview_manager import InterviewManager
        dialog = InterviewManager(self.winfo_toplevel(), 
                                 self.app_data['id'], 
                                 self.app_data['company_name'], 
                                 self.app_data['role_name'])

class Dashboard(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._search_timer = None
        self._render_job = None
        self.setup_ui()
        self.refresh_stats()
        self.refresh_list()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Top Bar: Search and Stats
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        
        # Search Bar
        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(self.top_frame, placeholder_text="Search company or role...", width=300, textvariable=self.search_var)
        self.search_entry.pack(side="left", padx=(0, 20))
        self.search_var.trace_add("write", self.on_search_change)

        # Stats Area
        self.stats_frame = ctk.CTkFrame(self.top_frame, fg_color="transparent")
        self.stats_frame.pack(side="right")
        
        self.total_apps_card = StatsCard(self.stats_frame, "Total Applications", 0)
        self.total_apps_card.pack(side="left", padx=10)
        
        self.active_apps_card = StatsCard(self.stats_frame, "Interviewing", 0)
        self.active_apps_card.pack(side="left", padx=10)

        # Main List Area
        self.list_frame = ctk.CTkFrame(self)
        self.list_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        
        # Headers for the list
        self.header_frame = ctk.CTkFrame(self.list_frame, height=40)
        self.header_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(self.header_frame, text="Company", font=("Arial", 12, "bold"), width=200, anchor="w").pack(side="left", padx=10)
        ctk.CTkLabel(self.header_frame, text="Role", font=("Arial", 12, "bold"), width=200, anchor="w").pack(side="left", padx=10)
        ctk.CTkLabel(self.header_frame, text="Status", font=("Arial", 12, "bold"), width=120, anchor="w").pack(side="left", padx=10)
        ctk.CTkLabel(self.header_frame, text="Date", font=("Arial", 12, "bold"), width=120, anchor="w").pack(side="left", padx=10)

        # Scrollable area for items
        self.scrollable_frame = ctk.CTkScrollableFrame(self.list_frame)
        self.scrollable_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Bottom Bar: Actions
        self.action_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 10))
        
        self.add_btn = ctk.CTkButton(self.action_frame, text="+ Add Application", command=self.on_add_application)
        self.add_btn.pack(side="left")

        self.settings_btn = ctk.CTkButton(self.action_frame, text="Settings", width=100, command=self.on_open_settings)
        self.settings_btn.pack(side="right")

    def refresh_data(self):
        """Deprecated: Use refresh_stats and refresh_list individually."""
        self.refresh_stats()
        self.refresh_list()

    def refresh_stats(self):
        total, interviewing = get_stats()
        self.total_apps_card.update_value(total)
        self.active_apps_card.update_value(interviewing)

    def refresh_list(self):
        # Cancel any pending render job
        if self._render_job:
            self.after_cancel(self._render_job)
            self._render_job = None

        # Clear existing
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        search_query = self.search_var.get()
        apps = get_applications(search_query)
        
        # Start batch rendering
        self._render_chunk(apps, 0)

    def _render_chunk(self, apps_list, index, chunk_size=15):
        """Renders items in batches to prevent UI freeze."""
        end_index = min(index + chunk_size, len(apps_list))
        
        for i in range(index, end_index):
            app = apps_list[i]
            # Use self.refresh_data for now as callback, or better, just stats/re-sort
            item = AppListItem(self.scrollable_frame, app, self.refresh_stats) 
            item.pack(fill="x", pady=2)
        
        if end_index < len(apps_list):
            self._render_job = self.after(10, lambda: self._render_chunk(apps_list, end_index, chunk_size))
        else:
            self._render_job = None

    def on_search_change(self, *args):
        if self._search_timer:
            self.after_cancel(self._search_timer)
        self._search_timer = self.after(300, self.refresh_list)

    def on_add_application(self):
        dialog = AddAppDialog(self.winfo_toplevel(), self.save_new_application)

    def on_open_settings(self):
        from .setup_wizard import SetupWizard
        dialog = SetupWizard(self.winfo_toplevel(), self.refresh_data)

    def save_new_application(self, company, role):
        try:
            # 1. Create Folder and templates
            folder_path = create_application_folder(company, role)
            
            # 2. Update Database
            add_application(company, role, folder_path)
            
            # 3. Refresh UI
            self.refresh_data()
            
            # 4. Open Folder
            open_folder(folder_path)
            
            messagebox.showinfo("Success", f"Application for {company} created successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create application: {e}")
