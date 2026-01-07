import customtkinter as ctk
import os
from .add_app_dialog import AddAppDialog
from ..core.database import add_application, get_applications, get_stats, update_application_status
from ..core.file_ops import create_application_folder, open_folder
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
        # Optimized: Flat widgets (no corner radius) for fastest rendering
        super().__init__(parent, height=50, corner_radius=0) 
        self.app_data = app_data
        self.on_refresh = on_refresh
        self.setup_ui()

    def setup_ui(self):
        # Use single formatted label instead of multiple labels with tooltips
        company = self.app_data['company_name'][:25] + ("..." if len(self.app_data['company_name']) > 25 else "")
        role = self.app_data['role_name'][:25] + ("..." if len(self.app_data['role_name']) > 25 else "")
        
        # Company and Role in single labels
        ctk.CTkLabel(self, text=company, width=200, anchor="w").pack(side="left", padx=10)
        ctk.CTkLabel(self, text=role, width=200, anchor="w").pack(side="left", padx=10)
        
        # Status dropdown
        self.status_var = ctk.StringVar(value=self.app_data['status'])
        self.status_menu = ctk.CTkOptionMenu(self, 
                                           values=["Applied", "Interviewing", "Rejected", "Offer", "Ghosted"],
                                           variable=self.status_var,
                                           command=self.on_status_change,
                                           width=120)
        self.status_menu.pack(side="left", padx=10)
        
        date_str = self.app_data['created_at'].split(' ')[0]
        ctk.CTkLabel(self, text=date_str, width=120, anchor="w").pack(side="left", padx=10)

        # Actions - Pack directly to the right
        self.interview_btn = ctk.CTkButton(self, text="Interviews", width=90, command=self.on_open_interviews)
        self.interview_btn.pack(side="right", padx=5)

        # Folder check and binding
        exists = os.path.exists(self.app_data['folder_path'])
        
        # Bind double click to open folder
        self.bind("<Double-1>", lambda e: self.on_open_folder())
        for child in self.winfo_children():
            if not isinstance(child, (ctk.CTkButton, ctk.CTkOptionMenu)):
                child.bind("<Double-1>", lambda e: self.on_open_folder())

        if not exists:
            # Change color of labels if path is missing
            for child in self.winfo_children():
                if isinstance(child, ctk.CTkLabel):
                    child.configure(text_color="red")

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
        self._resize_timer = None
        self._is_resizing = False
        self._last_size = None
        self.sort_order = "DESC"
        
        # Virtual scrolling
        self._all_apps = []
        self._visible_items = []
        self.ITEM_HEIGHT = 54  # Height of each AppListItem
        
        self.setup_ui()
        self.refresh_stats()
        self.refresh_list()
        
        # Bind resize event for throttling
        self.bind("<Configure>", self._on_resize)

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Top Bar: Search and Stats
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        
        # Search Bar
        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(self.top_frame, placeholder_text="Search company or role...", width=300, textvariable=self.search_var)
        self.search_entry.pack(side="left", padx=(0, 10))
        # Bind Enter key to search
        self.search_entry.bind("<Return>", lambda e: self.refresh_list())
        
        self.search_btn = ctk.CTkButton(self.top_frame, text="Search", width=80, command=self.refresh_list)
        self.search_btn.pack(side="left", padx=(0, 20))

        # Show All Toggle
        self.show_all_var = ctk.BooleanVar(value=False)
        self.show_all_switch = ctk.CTkSwitch(self.top_frame, text="Show All", variable=self.show_all_var, command=self.refresh_list)
        self.show_all_switch.pack(side="left", padx=(0, 20))

        # Reload Button
        self.reload_btn = ctk.CTkButton(self.top_frame, text="Scan & Reload", width=120, command=self.on_reload)
        self.reload_btn.pack(side="left")

        # Hidden sort variable to maintain logic
        self.sort_var = ctk.StringVar(value="Date")

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
        
        self.comp_header = ctk.CTkLabel(self.header_frame, text="Company ↕", font=("Arial", 12, "bold"), width=200, anchor="w", cursor="hand2")
        self.comp_header.pack(side="left", padx=10)
        self.comp_header.bind("<Button-1>", lambda e: self.on_header_click("Company"))

        ctk.CTkLabel(self.header_frame, text="Role", font=("Arial", 12, "bold"), width=200, anchor="w").pack(side="left", padx=10)
        ctk.CTkLabel(self.header_frame, text="Status", font=("Arial", 12, "bold"), width=120, anchor="w").pack(side="left", padx=10)
        
        self.date_header = ctk.CTkLabel(self.header_frame, text="Date ↕", font=("Arial", 12, "bold"), width=120, anchor="w", cursor="hand2")
        self.date_header.pack(side="left", padx=10)
        self.date_header.bind("<Button-1>", lambda e: self.on_header_click("Date"))

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
        self._visible_items.clear()

        search_query = self.search_var.get()
        sort_by = self.sort_var.get()
        
        self._all_apps = get_applications(search_query, sort_by=sort_by, sort_order=self.sort_order)
        
        # Limit to 20 if Show All is off and not searching
        if not self.show_all_var.get() and not search_query:
            self._all_apps = self._all_apps[:20]
        
        # Render list in chunks for performance
        self._render_chunk(0)

    def _render_chunk(self, index, chunk_size=30):
        """Renders items in batches to populate the scroll area without freezing."""
        if self._is_resizing:
            self._render_job = self.after(100, lambda: self._render_chunk(index, chunk_size))
            return
            
        end_index = min(index + chunk_size, len(self._all_apps))
        
        for i in range(index, end_index):
            app = self._all_apps[i]
            item = AppListItem(self.scrollable_frame, app, self.refresh_stats)
            item.pack(fill="x", pady=2)
            self._visible_items.append(item)
            
        if end_index < len(self._all_apps):
            self._render_job = self.after(20, lambda: self._render_chunk(end_index, chunk_size))
        else:
            self._render_job = None

    def _on_resize(self, event=None):
        """Handle window resize events with throttling and filtering"""
        # Only respond to resize of this widget, not children
        if event and event.widget != self:
            return
            
        # Check if size actually changed
        current_size = (self.winfo_width(), self.winfo_height())
        if self._last_size == current_size:
            return
        self._last_size = current_size
        
        self._is_resizing = True
        if self._resize_timer:
            self.after_cancel(self._resize_timer)
        self._resize_timer = self.after(300, self._on_resize_complete)
    
    def _on_resize_complete(self):
        """Resume rendering after resize is complete"""
        self._is_resizing = False
        # No need to re-render everything on resize since pack handles layout

    def on_search_change(self, *args):
        if self._search_timer:
            self.after_cancel(self._search_timer)
        self._search_timer = self.after(300, self.refresh_list)

    def on_header_click(self, column):
        if self.sort_var.get() == column:
            # Toggle order
            self.sort_order = "ASC" if self.sort_order == "DESC" else "DESC"
        else:
            # New column, set default order
            self.sort_var.set(column)
            self.sort_order = "DESC" if column == "Date" else "ASC"
        
        # Update header icons to show direction
        comp_text = "Company " + ("↑" if (column == "Company" and self.sort_order == "ASC") else 
                                   "↓" if (column == "Company" and self.sort_order == "DESC") else "↕")
        date_text = "Date " + ("↑" if (column == "Date" and self.sort_order == "ASC") else 
                                "↓" if (column == "Date" and self.sort_order == "DESC") else "↕")
        
        self.comp_header.configure(text=comp_text)
        self.date_header.configure(text=date_text)
        
        self.refresh_list()

    def on_add_application(self):
        dialog = AddAppDialog(self.winfo_toplevel(), self.save_new_application)

    def on_open_settings(self):
        from .setup_wizard import SetupWizard
        dialog = SetupWizard(self.winfo_toplevel(), self.refresh_data)

    def on_reload(self):
        """Scans the root folder for any new directories and removes records for missing folders."""
        from ..core.config_mgr import get_active_root
        from ..core.file_ops import scan_for_existing_applications
        from ..core.database import add_application, application_exists, get_applications, delete_application
        
        root_path = get_active_root()
        if not root_path:
            return

        # 1. Check for missing folders and remove from DB
        # Fetch all from DB (no filters) to verify existence
        db_apps = get_applications()
        removed_count = 0
        for app in db_apps:
            if not os.path.exists(app['folder_path']):
                delete_application(app['id'])
                removed_count += 1

        # 2. Check for new folders on disk and add to DB
        found_apps = scan_for_existing_applications(root_path)
        added_count = 0
        for app in found_apps:
            if not application_exists(app['company'], app['role']):
                add_application(app['company'], app['role'], app['path'])
                added_count += 1
        
        # Refresh the UI
        self.refresh_stats()
        self.refresh_list()
        
        msg = "Scan Complete!\n"
        if added_count > 0 or removed_count > 0:
            if added_count > 0:
                msg += f"- Imported {added_count} new applications\n"
            if removed_count > 0:
                msg += f"- Removed {removed_count} broken records (folders missing)\n"
            messagebox.showinfo("Scan Results", msg)
        else:
            messagebox.showinfo("Scan Results", "Everything is already in sync!")

    def save_new_application(self, company, role):
        try:
            # Check if exists
            from ..core.database import application_exists, count_applications_with_name
            final_role = role
            if application_exists(company, role):
                if not messagebox.askyesno("Duplicate Entry", 
                    f"An application for '{company}' - '{role}' already exists.\n\nDo you want to create another one with an index?"):
                    return
                
                # Generate indexed name
                count = count_applications_with_name(company, role)
                final_role = f"{role} ({count + 1})"

            # 1. Create Folder and templates
            folder_path = create_application_folder(company, final_role)
            
            # 2. Update Database
            add_application(company, final_role, folder_path)
            
            # 3. Refresh UI
            self.refresh_data()
            
            # 4. Open Folder
            open_folder(folder_path)
            
            messagebox.showinfo("Success", f"Application for {company} created successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create application: {e}")
