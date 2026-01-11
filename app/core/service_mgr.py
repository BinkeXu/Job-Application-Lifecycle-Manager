import os
import subprocess
import sys
import threading
import time
from pathlib import Path

# This class handles starting and stopping the .NET Background Service.
# It uses the "Singleton" pattern, meaning there is only ever ONE manager 
# running at a time, even if you try to create it multiple times.
class ServiceManager:
    _instance = None
    _process = None

    def __new__(cls):
        # This part ensures that only one instance of ServiceManager exists.
        if cls._instance is None:
            cls._instance = super(ServiceManager, cls).__new__(cls)
        return cls._instance

    def get_service_path(self):
        """
        Calculates the location of the JALM.Service.exe file.
        It needs to handle two cases:
        1. When running as a normal Python script (Developer mode).
        2. When bundled inside a single .exe file (Production mode).
        """
        if hasattr(sys, "_MEIPASS"):
            # If sys._MEIPASS exists, it means PyInstaller has extracted 
            # our files to a temporary folder. The service is right there!
            base_path = Path(sys._MEIPASS)
            service_path = base_path / "JALM.Service.exe"
        else:
            # If we are running as a script, we look for the file in the 
            # .NET project's publish or debug folders.
            base_path = Path(__file__).parent.parent.parent
            service_path = base_path / "JALM.Service" / "bin" / "Release" / "net8.0" / "win-x64" / "publish" / "JALM.Service.exe"
            
            if not service_path.exists():
                # Fallback to Debug if Release doesn't exist (helpful for developers)
                service_path = base_path / "JALM.Service" / "bin" / "Debug" / "net8.0" / "JALM.Service.exe"

        return service_path

    def start_service(self):
        """
        Launches the JALM.Service.exe in the background.
        It won't show a console window, so it stays hidden from the user.
        """
        # If the service is already running, don't start it again.
        if self._process and self._process.poll() is None:
            return

        service_path = self.get_service_path()
        if not service_path.exists():
            print(f"Service executable not found at: {service_path}")
            return

        print(f"Starting Background Service: {service_path}")
        try:
            # When running as an EXE, we need to tell the .NET service where the 
            # main application folder is, so it can find 'config.json'.
            # sys.executable gives us the path to the running .exe.
            executable_dir = str(Path(sys.executable).parent)
            
            # Create a copy of the current environment and add our custom variable.
            env = os.environ.copy()
            env["JALM_CONFIG_DIR"] = executable_dir

            # CREATE_NO_WINDOW (0x08000000) makes the process run invisibly.
            # This is important so the user doesn't see a random black box.
            self._process = subprocess.Popen(
                [str(service_path)],
                creationflags=0x08000000,
                cwd=str(service_path.parent), # Ensure it runs in its own directory
                env=env
            )
        except Exception as e:
            print(f"Failed to start background service: {e}")

    def stop_service(self):
        """
        Safely shuts down the background service.
        This is called automatically when the Python GUI is closed.
        """
        if self._process:
            print("Stopping Background Service...")
            # 'terminate' asks the service to close nicely.
            self._process.terminate()
            try:
                # Wait up to 5 seconds for it to finish.
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # If it takes too long, force it to close immediately.
                self._process.kill()
            self._process = None
