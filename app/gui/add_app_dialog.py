import customtkinter as ctk
from tkinter import messagebox

class AddAppDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_save_callback):
        super().__init__(parent)
        # The 'geometry' sets the size of the window (Width x Height).
        self.geometry("450x500") # Increased height to fit the Job Description box.
        self.on_save_callback = on_save_callback
        
        # 'transient' and 'grab_set' make this a "Modal" window.
        # This means you must finish adding the job before you can go back to the dashboard.
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

        # Job Description
        ctk.CTkLabel(self, text="Job Description:").grid(row=3, column=0, sticky="w", padx=35, pady=(15, 5))
        self.jd_text = ctk.CTkTextbox(self, height=150)
        self.jd_text.grid(row=4, column=0, sticky="ew", padx=30)

        # Save Button
        self.save_btn = ctk.CTkButton(self, text="Create Application", command=self.on_save)
        self.save_btn.grid(row=5, column=0, pady=30)

        # Bind Enter key to submit (only for entries, textbox handles Enter naturally)
        self.company_entry.bind("<Return>", lambda e: self.on_save())
        self.role_entry.bind("<Return>", lambda e: self.on_save())

    def on_save(self):
        """Called when the user clicks 'Create Application'."""
        company = self.company_entry.get().strip()
        role = self.role_entry.get().strip()
        # We grab the text from the big box (1.0 means start, end-1c means exclude last newline).
        description = self.jd_text.get("1.0", "end-1c").strip()

        if not company or not role:
            messagebox.showwarning("Incomplete Data", "Please enter both Company and Role.")
            return

        # Pass all three pieces of data back to the dashboard to handle the saving.
        self.on_save_callback(company, role, description)
        self.destroy()
