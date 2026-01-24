import atexit
import signal
import sys
import customtkinter as ctk
from app.core.config_mgr import is_config_complete
from app.gui.setup_wizard import SetupWizard
from app.core.database import init_db
from app.core.service_mgr import ServiceManager

# This is the entry point of the entire JALM application.
# It creates the main window and manages the app's overall lifecycle.
class JALMApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # 1. Basic Window Setup
        self.title("Job Application Lifecycle Manager (JALM)")
        self.geometry("1000x600")
        self.minsize(800, 500)  # Prevent the window from being resized too small

        # 2. Database Preparation
        # This creates the necessary SQLite tables if they don't exist yet.
        init_db()

        # 3. Hybrid Sync Startup
        # We start the .NET background service right away.
        # This service handles real-time folder watching and document generation.
        self.service_mgr = ServiceManager()
        self.service_mgr.start_service()

        # 4. Safe Shutdown
        # 'atexit' ensures that when the user closes this Python app, 
        # the background .NET service is also stopped automatically.
        atexit.register(self.service_mgr.stop_service)
        
        # Bind close handler to ensure clean shutdown
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 5. Initialization Logic
        # If the user hasn't finished the initial setup (name, root folder, etc.), 
        # we hide the main window and show the Setup Wizard instead.
        if not is_config_complete():
            self.withdraw() # Hide main window for now
            self.show_setup_wizard()
        else:
            self.init_main_ui()

    def show_setup_wizard(self):
        """Displays the step-by-step installation guide (Setup Wizard)."""
        wizard = SetupWizard(self, self.on_setup_complete)
        wizard.focus_set()

    def on_setup_complete(self):
        """Called once the user finished the Setup Wizard."""
        self.deiconify() # Bring the main window back to the front
        self.init_main_ui()

    def init_main_ui(self):
        """Loads and displays the main Dashboard with all your applications."""
        from app.gui.dashboard import Dashboard
        self.dashboard = Dashboard(self)
        self.dashboard.pack(fill="both", expand=True)

    def on_closing(self):
        """Handle window close event with proper cleanup."""
        try:
            # IMPORTANT: Destroy all children first. This triggers the <Destroy> event
            # in the Dashboard, which cancels all active background timers.
            # This prevents "invalid command name" errors after the app exits.
            for widget in self.winfo_children():
                widget.destroy()
        except Exception:
            pass
        
        # Quit the mainloop first to stop processing events, then destroy the main window.
        self.quit()
        self.destroy()

# This check prevents code from running if this file is imported elsewhere.
if __name__ == "__main__":
    app = JALMApp()
    
    # Define a handler for system signals like Ctrl+C (SIGINT).
    # This ensures that even if the app is killed from the terminal,
    # the proper cleanup sequence is still triggered.
    def signal_handler(sig, frame):
        # Trigger the same cleanup logic used for normal window closing.
        app.on_closing()
        sys.exit(0)
    
    # Register the signal handler.
    signal.signal(signal.SIGINT, signal_handler)
    
    app.mainloop() # Start the UI event loop!
