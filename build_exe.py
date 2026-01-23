import PyInstaller.__main__
import os
import shutil
import customtkinter

# Get the directory where customtkinter is installed to collect its data files (json/tcl)
ctk_path = os.path.dirname(customtkinter.__file__)

# Paths to include
# We include the .NET Service executable so service_mgr.py can find it in sys._MEIPASS
service_exe = os.path.join(
    "JALM.Service", "bin", "Release", "net8.0", "win-x64", "publish", "JALM.Service.exe"
)

# Build the argument list for PyInstaller
args = [
    'main.py',                   # Entry point
    '--name=JALM',               # Name of the output EXE
    '--onefile',                 # Bundle into a single executable
    '--noconsole',               # Don't show the command prompt when running
    '--clean',                   # Clean cache before build
    # Include customtkinter theme/data files
    f'--add-data={ctk_path};customtkinter/',
    # Include the .NET Service EXE in the root of the bundle
    f'--add-data={service_exe};.',
    # Add hidden imports if necessary
    '--hidden-import=PIL._tkinter_guess_binary',
    '--hidden-import=matplotlib.backends.backend_tkagg',
]

print(f"Starting build for JALM.exe...")
print(f"Using customtkinter from: {ctk_path}")
print(f"Including Service from: {service_exe}")

# Run PyInstaller
PyInstaller.__main__.run(args)

print("\nBuild complete! Check the 'dist' folder for JALM.exe")
