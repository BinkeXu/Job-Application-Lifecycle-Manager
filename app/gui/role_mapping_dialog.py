import customtkinter as ctk
from tkinter import messagebox
from ..core.database import get_all_role_mappings, update_role_mapping, clear_all_role_mappings

# This list matches the exact categories defined in the LLM prompt.
CATEGORIES = [
    "Software Engineer",
    "Data Engineer",
    "Data Scientist",
    "Data Analyst",
    "Analyst - other",
    "Graduate Program",
    "Machine Learning Engineer",
    "DevOps / Infrastructure",
    "Product Manager",
    "UI/UX Designer",
    "Cybersecurity",
    "IT Support",
    "Sales / Marketing",
    "Other"
]

class RoleMappingDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_close_callback=None):
        super().__init__(parent)
        self.title("Manage Role Classifications")
        self.geometry("600x600")
        
        # UI Polish: Center the dialog
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (600 // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (600 // 2)
        self.geometry(f"+{x}+{y}")
        
        self.on_close_callback = on_close_callback
        
        # Close event
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        # 1. Header & Actions
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(self.header_frame, text="Current Classifications", font=("Arial", 16, "bold")).pack(side="left")
        
        self.reclassify_btn = ctk.CTkButton(self.header_frame, text="Re-Classify All with LLM", 
                                            fg_color="#EF4444", hover_color="#B91C1C", 
                                            command=self.confirm_reclassify)
        self.reclassify_btn.pack(side="right")
        
        # 2. Scrollable Data Grid
        self.grid_frame = ctk.CTkScrollableFrame(self)
        self.grid_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Grid Headers
        ctk.CTkLabel(self.grid_frame, text="Original Role", font=("Arial", 12, "bold"), anchor="w").grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        ctk.CTkLabel(self.grid_frame, text="Mapped Group", font=("Arial", 12, "bold"), anchor="w").grid(row=0, column=1, sticky="ew", padx=10, pady=5)
        
        self.grid_frame.grid_columnconfigure(0, weight=1)
        self.grid_frame.grid_columnconfigure(1, weight=1)
        
        self.row_widgets = []
        
        # 3. Footer
        self.close_btn = ctk.CTkButton(self, text="Close", fg_color="gray", command=self.on_close)
        self.close_btn.pack(side="bottom", pady=20)
        
    def load_data(self):
        # Clear existing rows
        for widget in self.row_widgets:
            widget.destroy()
        self.row_widgets.clear()
        
        mappings = get_all_role_mappings()
        
        if not mappings:
            lbl = ctk.CTkLabel(self.grid_frame, text="No roles have been classified yet.\nOpen the Analytics Report to let the LLM classify your data.", text_color="gray")
            lbl.grid(row=1, column=0, columnspan=2, pady=30)
            self.row_widgets.append(lbl)
            return

        for index, row in enumerate(mappings):
            original_role = row[0]
            mapped_category = row[1]
            
            # Row Frame
            lbl_role = ctk.CTkLabel(self.grid_frame, text=original_role, anchor="w")
            lbl_role.grid(row=index+1, column=0, sticky="ew", padx=10, pady=5)
            
            # Use the categories list, ensuring the current value is always included even if it's off-list
            current_categories = list(CATEGORIES)
            if mapped_category and mapped_category not in current_categories:
                current_categories.append(mapped_category)
                
            opt_category = ctk.CTkOptionMenu(
                self.grid_frame, 
                values=current_categories,
                command=lambda new_val, role=original_role: self.on_category_changed(role, new_val)
            )
            opt_category.set(mapped_category)
            opt_category.grid(row=index+1, column=1, sticky="ew", padx=10, pady=5)
            
            self.row_widgets.extend([lbl_role, opt_category])

    def on_category_changed(self, original_role, new_category):
        """Called automatically when the user selects a new dropdown value."""
        update_role_mapping(original_role, new_category)
        
    def confirm_reclassify(self):
        """Asks for confirmation before clearing the cache."""
        confirm = messagebox.askyesno(
            "Re-Classify All",
            "This will delete all your manual corrections and force the LLM to process all unique roles from scratch the next time you open the report.\n\nAre you sure?",
            parent=self
        )
        if confirm:
            clear_all_role_mappings()
            self.load_data()
            messagebox.showinfo("Success", "Cache cleared. Re-classification will occur when the report is next generated.", parent=self)
            
    def on_close(self):
        if self.on_close_callback:
            self.on_close_callback()
        self.destroy()
