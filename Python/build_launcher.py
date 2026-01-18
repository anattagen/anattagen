import PyInstaller.__main__
import os
import sys

def build():
    # Define paths
    
    base_dir = os.path.dirname(os.path.abspath(__file__))    
    script_path = os.path.join(base_dir, "Launcher.py")
    project_root = os.path.dirname(base_dir)
    icon_path = os.path.join(base_dir, "./../assets", "anattagen.ico")
    splash_path = os.path.join(base_dir, "./../assets", "splash.png")
    dist_dir = os.path.join(base_dir, "./../bin")
    build_dir = os.path.join(base_dir, "./../build")

    # Ensure bin directory exists
    if not os.path.exists(dist_dir):
        os.makedirs(dist_dir)

    print(f"Building Launcher from: {script_path}")
    print(f"Output directory: {dist_dir}")

    # PyInstaller arguments
    args = [
        script_path,
        '--onefile',                # Create a single executable file
        '--name=Launcher',          # Name of the executable
        f'--distpath={dist_dir}',   # Output directory
        f'--specpath={project_root}', # Generate spec file in project root
        f'--workpath={build_dir}',  # Temporary build directory
        '--clean',                  # Clean cache before building
        '--hidden-import=pygame',   # Pygame is imported inside a function
        '--hidden-import=win32timezone', # Often needed for pywin32
        '--noconsole',            # Hide console window (useful for final release)
    ]

    # Add icon if it exists
    if os.path.exists(icon_path):
        args.append(f'--icon={icon_path}')
        
    # Add splash screen if it exists
    # Note: Tcl/Tk is required for splash screens. Disabled to prevent build errors if missing.
    # if os.path.exists(splash_path):
    #     args.append(f'--splash={splash_path}')
    
    # Add the project root to path so imports work during analysis
    sys.path.insert(0, base_dir)

    # Run PyInstaller
    PyInstaller.__main__.run(args)

    print(f"\nBuild complete. Executable located at: {os.path.join(dist_dir, 'Launcher.exe')}")

if __name__ == "__main__":
    build()