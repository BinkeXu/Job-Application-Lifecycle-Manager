import customtkinter as ctk
from tkinter import messagebox

class AddAppDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_save_callback):
        super().__init__(parent)
        self.title("Add New Job Application")
        self.geometry("400x300")
        self.on_save_callback = on_save_callback
        
        # Make it modal
        self.transient(parent)
        self.grab_set()

        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="New Application", font=("Arial", 20, "bold")).grid(row=0, column=0, pady=20)

        # Company Name
        frame1 = ctk.CTkFrame(self, fg_color="transparent")
        frame1.grid(row=1, column=0, sticky="ew", padx=30, pady=5)
        ctk.CTkLabel(frame1, text="Company:").pack(side="left")
        self.company_entry = ctk.CTkEntry(frame1, width=200)
        self.company_entry.pack(side="right")
        self.company_entry.focus_set()

        # Role Name
        frame2 = ctk.CTkFrame(self, fg_color="transparent")
        frame2.grid(row=2, column=0, sticky="ew", padx=30, pady=5)
        ctk.CTkLabel(frame2, text="Role:").pack(side="left")
        self.role_entry = ctk.CTkEntry(frame2, width=200)
        self.role_entry.pack(side="right")

        # Save Button
        self.save_btn = ctk.CTkButton(self, text="Create Application", command=self.on_save)
        self.save_btn.grid(row=3, column=0, pady=30)

        # Bind Enter key to submit
        self.company_entry.bind("<Return>", lambda e: self.on_save())
        self.role_entry.bind("<Return>", lambda e: self.on_save())

    def on_save(self):
        company = self.company_entry.get().strip()
        role = self.role_entry.get().strip()

        if not company or not role:
            messagebox.showwarning("Incomplete Data", "Please enter both Company and Role.")
            return

        self.on_save_callback(company, role)
        self.destroy()
