import customtkinter as ctk
import os
from .add_app_dialog import AddAppDialog
from ..core.database import add_application, get_applications, get_stats, update_application_status, delete_application
from ..core.file_ops import create_application_folder, open_folder
from tkinter import messagebox, Menu, filedialog

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
                                           values=["Applied", "Interviewed", "Rejected", "Offer", "Ghosted"],
                                           variable=self.status_var,
                                           command=self.on_status_change,
                                           width=120)
        self.status_menu.pack(side="left", padx=10)
        
        # Initialize status color
        self._update_status_color(self.app_data['status'])
        
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
        
        # Context Menu
        self.setup_context_menu()

        if not exists:
            # Change color of labels if path is missing
            for child in self.winfo_children():
                if isinstance(child, ctk.CTkLabel):
                    child.configure(text_color="red")

    def on_status_change(self, new_status):
        """
        Updates the application status both in the database and the UI.
        Ensures that analytics modules will generate reports based on the newest state.
        """
        update_application_status(self.app_data['id'], new_status)
        self._update_status_color(new_status)
        self.on_refresh()

    def _update_status_color(self, status):
        # Default Theme Colors (Dark Blue / Light Blue)
        # We need to set both fg_color and button_color
        if status == "Rejected":
            # Red
            color = "#C42B1C" 
            hover = "#8F1F14"
            self.status_menu.configure(fg_color=color, button_color=color, button_hover_color=hover)
        elif status == "Ghosted":
            # Yellow/Orange
            color = "#D97706" 
            hover = "#B45309"
            self.status_menu.configure(fg_color=color, button_color=color, button_hover_color=hover)
        elif status == "Offer":
            # Green
            color = "#10B981"
            hover = "#059669"
            self.status_menu.configure(fg_color=color, button_color=color, button_hover_color=hover)
        elif status == "Interviewed":
            # Purple
            color = "#8B5CF6"
            hover = "#7C3AED"
            self.status_menu.configure(fg_color=color, button_color=color, button_hover_color=hover)
        else:
            # Default Blue
            self.status_menu.configure(fg_color=["#3B8ED0", "#1F6AA5"], 
                                     button_color=["#3B8ED0", "#1F6AA5"], 
                                     button_hover_color=["#36719F", "#27577D"])

    def setup_context_menu(self):
        self.context_menu = Menu(self, tearoff=0)
        self.context_menu.add_command(label="Delete Record", command=self.on_delete_record)
        
        # Bind right click to the frame itself
        self.bind("<Button-3>", self.show_context_menu)
        
        # KEY FIX: Bind to all children too!
        # If we don't do this, clicking on a Label inside the Frame won't trigger the menu.
        for child in self.winfo_children():
            if not isinstance(child, (ctk.CTkButton, ctk.CTkOptionMenu)):
                child.bind("<Button-3>", self.show_context_menu)

    def show_context_menu(self, event):
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def on_delete_record(self):
        if messagebox.askyesno("Confirm Delete", 
                             f"Are you sure you want to delete the record for:\n\n{self.app_data['company_name']} - {self.app_data['role_name']}?\n\nNote: This only deletes the database record. The folder will NOT be deleted."):
            delete_application(self.app_data['id'])
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
        self._refresh_job = None
        self._is_resizing = False
        self._last_size = None
        self.sort_order = "DESC"
        
        # Virtual scrolling
        self._all_apps = []
        self._visible_items = []
        self.ITEM_HEIGHT = 54  # Height of each AppListItem
        
        self.setup_ui()
        self._last_app_count = 0
        
        self.refresh_stats()
        self.refresh_list()
        
        # Start auto-refresh poller
        self._setup_auto_refresh()
        
        # Bind resize event for throttling
        self.bind("<Configure>", self._on_resize)
        
        # Bind destroy event for cleanup
        self.bind("<Destroy>", self._on_destroy_event)

    def _setup_auto_refresh(self):
        """
        Sets up a 'heartbeat' for the UI.
        Every 10 seconds, it checks if the .NET service has added new jobs 
        or if any files were moved, so the UI stays up-to-date automatically.
        """
        total, _ = get_stats()
        self._last_app_count = total
        total, _ = get_stats()
        self._last_app_count = total
        self._refresh_job = self.after(5000, self._auto_refresh)

    def _auto_refresh(self):
        """Periodically refreshes the list ONLY if the application count has changed."""
        if not self.winfo_exists():
            return
            
        # If you are typing in the search box, we pause the auto-refresh so we don't interrupt you.
        if not self.search_var.get():
            current_total, interviewing = get_stats()
            
            # If the number of jobs changed (Sync added a new folder!), update the UI.
            if current_total != self._last_app_count:
                self._last_app_count = current_total
                self.refresh_list()
                
                # Update the numbers at the top of the screen.
                self.total_apps_card.update_value(current_total)
                self.active_apps_card.update_value(interviewing)
        
        # Check again in 10 seconds.
        # Check again in 10 seconds.
        self._refresh_job = self.after(10000, self._auto_refresh)

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

        # Analytics Button
        self.analytics_btn = ctk.CTkButton(self.top_frame, text="Analytics", width=100, command=self.on_open_analytics)
        self.analytics_btn.pack(side="left", padx=(10, 0))

        # Hidden sort variable to maintain logic
        self.sort_var = ctk.StringVar(value="Date")

        # Stats Area
        self.stats_frame = ctk.CTkFrame(self.top_frame, fg_color="transparent")
        self.stats_frame.pack(side="right")
        
        self.total_apps_card = StatsCard(self.stats_frame, "Total Applications", 0)
        self.total_apps_card.pack(side="left", padx=10)
        
        self.active_apps_card = StatsCard(self.stats_frame, "Interviewed", 0)
        self.active_apps_card.pack(side="left", padx=10)

        self.ghosted_apps_card = StatsCard(self.stats_frame, "Ghosted (30d)", 0)
        self.ghosted_apps_card.pack(side="left", padx=10)

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

        self.export_btn = ctk.CTkButton(self.action_frame, text="Export Results", fg_color="#555555", width=120, command=self.on_export)
        self.export_btn.pack(side="left", padx=20)

        self.settings_btn = ctk.CTkButton(self.action_frame, text="Settings", width=100, command=self.on_open_settings)
        self.settings_btn.pack(side="right")

    def refresh_data(self):
        """Deprecated: Use refresh_stats and refresh_list individually."""
        self.refresh_stats()
        self.refresh_list()

    def refresh_stats(self):
        """Fetches the latest numbers and updates the cards at the top of the app."""
        total, interviewing = get_stats()
        self.total_apps_card.update_value(total)
        self.active_apps_card.update_value(interviewing)
        
        # The 'Ghosted' count is calculated by the .NET Background Service.
        # It saves it to a file called 'analytics.json'. We try to read it here.
        from ..core.config_mgr import get_active_root
        import json
        root = get_active_root()
        if root:
            analytics_path = os.path.join(root, "analytics.json")
            if os.path.exists(analytics_path):
                try:
                    with open(analytics_path, 'r') as f:
                        data = json.load(f)
                        # Update the 'Ghosted (30d)' card with the latest number!
                        self.ghosted_apps_card.update_value(data.get("Ghosted", 0))
                except:
                    # If the file is being written to by the service, just skip this update.
                    pass

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
        if not self.winfo_exists():
            return

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
        if not self.winfo_exists():
            return
            
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

    def on_open_analytics(self):
        from .analytics_view import AnalyticsDashboard
        # Prevent multiple windows
        if hasattr(self, 'analytics_window') and self.analytics_window.winfo_exists():
            self.analytics_window.lift()
            return
        self.analytics_window = AnalyticsDashboard(self)
        self.analytics_window.grab_set() # Modal-like behavior

    def on_open_settings(self):
        from .setup_wizard import SetupWizard
        dialog = SetupWizard(self.winfo_toplevel(), self.refresh_data)

    def on_reload(self):
        """Scans the root folder for any new directories and removes records for missing folders."""
        from ..core.config_mgr import get_active_root
        from ..core.file_ops import scan_for_existing_applications
        from ..core.database import add_application, get_applications, delete_application, remove_duplicates, update_application_date
        
        root_path = get_active_root()
        if not root_path:
            return

        # 1. Check for new folders on disk and add to DB
        # Also update timestamps for existing apps to ensure accuracy
        found_apps = scan_for_existing_applications(root_path)
        added_count = 0
        updated_count = 0
        
        # Get current DB state
        current_db_apps = get_applications()
        # Create a lookup map by (company, role)
        db_map = {(app['company_name'], app['role_name']): app['id'] for app in current_db_apps}

        for app in found_apps:
            key = (app['company'], app['role'])
            if key not in db_map:
                # Determine initial status
                # SYNC LOGIC: Check for existence of 'interviews.txt' on disk.
                # This file acts as a flag indicating the application has reached the interview stage.
                is_interviewed = app.get('has_interviews', False)
                # Add to DB (returns new ID)
                new_id = add_application(app['company'], app['role'], app['path'], app.get('created_at'))
                
                # If discovered as interviewed on disk, update the record immediately
                if is_interviewed:
                     from ..core.database import update_application_status
                     update_application_status(new_id, 'Interviewed')
                
                added_count += 1
            else:
                # Update date for existing app to stay in sync with filesystem
                app_id = db_map[key]
                update_application_date(app_id, app.get('created_at'))
                
                # STATUS SYNCHRONIZATION: Promote status to 'Interviewed' if notes were found on disk.
                # This ensures that external updates (like manual file movement) are reflected in the UI.
                if app.get('has_interviews'):
                    from ..core.database import get_application_by_id, update_application_status
                    current_record = get_application_by_id(app_id)
                    # Only promote if currently marked as 'Applied' to respect manual rejections/offers
                    if current_record and current_record['status'] == 'Applied':
                        update_application_status(app_id, 'Interviewed')
                        updated_count += 1
                
                updated_count += 1

        # 2. Remove duplicated records (same folder path)
        # We do this after scanning to catch any duplicates that might have been created
        duplicates_removed = remove_duplicates()

        # 3. Check for missing folders and remove from DB
        # Fetch fresh from DB after scan and duplicate removal
        db_apps = get_applications()
        removed_count = 0
        for app in db_apps:
            if not os.path.exists(app['folder_path']):
                delete_application(app['id'])
                removed_count += 1
        
        # Refresh the UI
        self.refresh_stats()
        self.refresh_list()
        
        msg = "Scan Complete!\n"
        total_removed = removed_count + duplicates_removed
        if added_count > 0 or total_removed > 0 or updated_count > 0:
            if added_count > 0:
                msg += f"- Imported {added_count} new applications\n"
            if total_removed > 0:
                msg += f"- Removed {total_removed} broken or duplicate records\n"
            if updated_count > 0:
                msg += f"- Synced dates for {updated_count} existing applications\n"
            messagebox.showinfo("Scan Results", msg)
        else:
            messagebox.showinfo("Scan Results", "Everything is already in sync!")

    def save_new_application(self, company, role, job_description=None, cv_template_path=None):
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
            folder_path, creation_time = create_application_folder(company, final_role, job_description, cv_template_path)
            
            # 2. Update Database
            add_application(company, final_role, folder_path, creation_time, job_description)
            
            # 3. Refresh UI
            self.refresh_data()
            
            # 4. Open Folder
            open_folder(folder_path)
            
            messagebox.showinfo("Success", f"Application for {company} created successfully!")
        except Exception as e:
            messagebox.showinfo("Success", f"Application for {company} created successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create application: {e}")

    def on_export(self):
        """Opens the export dialog."""
        # 1. Get current list (filtered by search)
        apps_to_export = self._all_apps
        if not apps_to_export:
            messagebox.showinfo("Export", "No applications found to export.")
            return

        search_query = self.search_var.get()
        
        # 2. Open Dialog
        from .export_dialog import ExportDialog
        from .export_dialog import ExportDialog
        ExportDialog(self.winfo_toplevel(), apps_to_export, search_query)

    def destroy(self):
        """Manual destroy override."""
        self._cancel_timers()
        super().destroy()

    def _on_destroy_event(self, event):
        """Handles the <Destroy> event to clean up timers if the widget is destroyed."""
        if event.widget == self:
            self._cancel_timers()

    def _cancel_timers(self):
        """Helper to cancel all active timers."""
        try:
            if self._refresh_job:
                self.after_cancel(self._refresh_job)
                self._refresh_job = None
            if self._render_job:
                self.after_cancel(self._render_job)
                self._render_job = None
            if self._resize_timer:
                self.after_cancel(self._resize_timer)
                self._resize_timer = None
            if self._search_timer:
                self.after_cancel(self._search_timer)
                self._search_timer = None
        except Exception:
            # Ignore errors if timers are already invalid
            pass
