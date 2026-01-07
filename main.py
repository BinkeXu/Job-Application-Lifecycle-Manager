import customtkinter as ctk
from app.core.config_mgr import is_config_complete
from app.gui.setup_wizard import SetupWizard
from app.core.database import init_db


class JALMApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Job Application Lifecycle Manager (JALM)")
        self.geometry("1000x600")
        self.minsize(800, 500)  # Prevent excessive small-window rendering

        # Initialize database
        init_db()

        if not is_config_complete():
            self.withdraw() # Hide main window while setup is running
            self.show_setup_wizard()
        else:
            self.init_main_ui()

    def show_setup_wizard(self):
        wizard = SetupWizard(self, self.on_setup_complete)
        wizard.focus_set()

    def on_setup_complete(self):
        self.deiconify() # Show main window
        self.init_main_ui()

    def init_main_ui(self):
        from app.gui.dashboard import Dashboard
        self.dashboard = Dashboard(self)
        self.dashboard.pack(fill="both", expand=True)

if __name__ == "__main__":
    app = JALMApp()
    app.mainloop()
