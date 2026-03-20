import customtkinter as ctk

class ReportDialog(ctk.CTkToplevel):
    """
    A detailed summary view that presents application performance metrics.
    Displays conversion rates and categorized breakdowns (Role, Company, Status).
    """
    def __init__(self, parent, metrics, date_range_text):
        super().__init__(parent)
        self.title(f"Analytics Report ({date_range_text})")
        self.geometry("1100x800")
        
        self.metrics = metrics
        
        # UI Polish: Center the report dialog.
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (1100 // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (800 // 2)
        self.geometry(f"+{x}+{y}")
        
        self.setup_ui()
        
    def setup_ui(self):
        """Builds the report layout: Header metrics cards followed by detailed tables."""
        # 1. High Level Summary (Conversion Metrics)
        self.summary_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.summary_frame.pack(fill="x", padx=20, pady=20)
        
        total = self.metrics["total_apps"]
        oa = self.metrics["oa_count"]
        hr = self.metrics["hr_call_count"]
        interviewed = self.metrics["interviews_secured"]
        offers = self.metrics["offers_count"]
        
        # Success Rate is the percentage of applications that successfully progressed to an interview.
        rate = (interviewed / total * 100) if total > 0 else 0
        
        # Split cards into two rows for better horizontal space and readability
        self.summary_row1 = ctk.CTkFrame(self.summary_frame, fg_color="transparent")
        self.summary_row1.pack(fill="x", pady=(0, 10))
        
        self.summary_row2 = ctk.CTkFrame(self.summary_frame, fg_color="transparent")
        self.summary_row2.pack(fill="x")
        
        # Top Row: Overarching Metrics
        self._create_card(self.summary_row1, "Total Apps", total, "#3B8ED0")
        self._create_card(self.summary_row1, "Success Rate", f"{rate:.1f}%", "#10B981")
        
        # Bottom Row: Funnel Pipeline
        self._create_card(self.summary_row2, "OA", oa, "#0891B2")
        self._create_card(self.summary_row2, "HR Call", hr, "#DB2777")
        self._create_card(self.summary_row2, "Interviewed", interviewed, "#8B5CF6")
        
        # 2. Detailed Breakdown Tables (Categorized Lists)
        self.tables_frame = ctk.CTkScrollableFrame(self)
        self.tables_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        # Bottom Actions
        self.close_btn = ctk.CTkButton(self, text="Close Report", width=150, fg_color="gray", hover_color="#4B4B4B", command=self.destroy)
        self.close_btn.pack(side="bottom", pady=(0, 20))
        
        # Use a 2-column grid to organize the breakdown tables.
        self.tables_frame.grid_columnconfigure(0, weight=1)
        self.tables_frame.grid_columnconfigure(1, weight=1)
        
        # 1. Specialized Roles Tables (Full Width)
        row_idx = 0
        
        def format_roles(roles_list):
            # Formats [ (Company, Role) ] into [ ("Company - Role", "-") ]
            return [(f"{row[0]} - {row[1]}", "-") for row in roles_list]
        
        if self.metrics["interview_roles_list"]:
            self._create_table(self.tables_frame, "Interviewed Roles", format_roles(self.metrics["interview_roles_list"]), row=row_idx, col=0, colspan=2, header_name="Application", title_color="#8B5CF6")
            row_idx += 1

        if self.metrics.get("oa_roles_list"):
            self._create_table(self.tables_frame, "OA Roles", format_roles(self.metrics["oa_roles_list"]), row=row_idx, col=0, colspan=2, header_name="Application", title_color="#0891B2")
            row_idx += 1

        if self.metrics.get("hr_call_roles_list"):
            self._create_table(self.tables_frame, "HR Call Roles", format_roles(self.metrics["hr_call_roles_list"]), row=row_idx, col=0, colspan=2, header_name="Application", title_color="#DB2777")
            row_idx += 1

        # 2. Status Table (Full Width)
        self._create_table(self.tables_frame, "By Status", self.metrics["by_status"], row=row_idx, col=0, colspan=2, header_name="Status")
        row_idx += 1
        
        # 3. Company & Role Tables (Side by Side)
        self._create_table(self.tables_frame, "Top Companies", self.metrics["by_company"], row=row_idx, col=0, header_name="Company")
        self._create_table(self.tables_frame, "Top Roles", self.metrics["by_role"], row=row_idx, col=1, header_name="Role")

    def _create_card(self, parent, title, value, color):
        """Helper to create color-coded metric cards at the top."""
        card = ctk.CTkFrame(parent, fg_color=color, corner_radius=10)
        card.pack(side="left", fill="both", expand=True, padx=8)
        
        ctk.CTkLabel(card, text=title, text_color="white", font=("Arial", 14)).pack(pady=(15, 5))
        ctk.CTkLabel(card, text=str(value), text_color="white", font=("Arial", 28, "bold")).pack(pady=(0, 15))

    def _create_table(self, parent, title, data, row, col, colspan=1, header_name="Name", title_color=None):
        """Helper to create structured data tables with headers and rows."""
        frame = ctk.CTkFrame(parent)
        frame.grid(row=row, column=col, columnspan=colspan, sticky="nsew", padx=10, pady=10)
        
        title_lbl = ctk.CTkLabel(frame, text=title, font=("Arial", 16, "bold"))
        if title_color:
            title_lbl.configure(text_color=title_color)
        title_lbl.pack(pady=10,anchor="w", padx=15)
        
        # Header Row
        header = ctk.CTkFrame(frame, height=30, fg_color="transparent")
        header.pack(fill="x", padx=10)
        ctk.CTkLabel(header, text=header_name, font=("Arial", 12, "bold"), anchor="w").pack(side="left", padx=5, expand=True, fill="x")
        ctk.CTkLabel(header, text="Count", font=("Arial", 12, "bold"), width=50, anchor="e").pack(side="right", padx=5)
        
        # Dynamic Rows based on database aggregation
        if not data:
             ctk.CTkLabel(frame, text="No data available", text_color="gray").pack(pady=20)
        else:
            for item in data:
                # item is a sqlite3.Row object or tuple
                name = item[0]
                count = item[1]
                
                row_frame = ctk.CTkFrame(frame, fg_color="transparent", height=30)
                row_frame.pack(fill="x", padx=10, pady=2)
                
                name_lbl = ctk.CTkLabel(row_frame, text=str(name), anchor="w")
                name_lbl.pack(side="left", padx=5, expand=True, fill="x")
                
                ctk.CTkLabel(row_frame, text=str(count), width=50, anchor="e").pack(side="right", padx=5)
