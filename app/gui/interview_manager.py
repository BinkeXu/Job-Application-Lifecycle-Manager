import customtkinter as ctk
from ..core.database import get_interviews, add_interview, get_application_by_id
from ..core.file_ops import append_interview_note
from tkinter import simpledialog, messagebox

class InterviewManager(ctk.CTkToplevel):
    def __init__(self, parent, app_id, company, role):
        super().__init__(parent)
        self.title(f"Interviews - {company} ({role})")
        self.geometry("600x500")
        self.app_id = app_id
        
        # Make it modal
        self.transient(parent)
        self.grab_set()

        self.setup_ui()
        self.refresh_list()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkLabel(self, text="Interview Log", font=("Arial", 20, "bold"))
        header.grid(row=0, column=0, pady=20)

        # Scrollable area for interviews
        self.scrollable_frame = ctk.CTkScrollableFrame(self)
        self.scrollable_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))

        # Add Button
        self.add_btn = ctk.CTkButton(self, text="+ Add Interview Note", command=self.on_add_interview)
        self.add_btn.grid(row=2, column=0, pady=(0, 20))

    def refresh_list(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        interviews = get_interviews(self.app_id)
        if not interviews:
            ctk.CTkLabel(self.scrollable_frame, text="No interviews logged yet.").pack(pady=20)
            return

        for interview in interviews:
            frame = ctk.CTkFrame(self.scrollable_frame)
            frame.pack(fill="x", pady=5, padx=5)
            
            title_text = f"Interview {interview['sequence']} - {interview['date'].split(' ')[0]}"
            ctk.CTkLabel(frame, text=title_text, font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(5, 0))
            
            notes_text = ctk.CTkTextbox(frame, height=80)
            notes_text.pack(fill="x", padx=10, pady=5)
            notes_text.insert("1.0", interview['notes'] or "")
            notes_text.configure(state="disabled")

    def on_add_interview(self):
        """Prompts the user for a note and saves it to both the database and a text file."""
        # Simple dialog to ask for the note.
        note = simpledialog.askstring("Interview Note", "Enter interview details/feedback:", parent=self)
        if note:
            try:
                # 1. Save to Database first. We get a 'sequence' number (e.g., Interview 1).
                sequence = add_interview(self.app_id, note)
                
                # 2. Find where the application's folder is on your computer.
                app = get_application_by_id(self.app_id)
                if app and app['folder_path']:
                    # 3. Append the note to the 'interviews.txt' file in that folder.
                    append_interview_note(app['folder_path'], sequence, note)
                
                # Update the list on the screen.
                self.refresh_list()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add interview: {e}")
