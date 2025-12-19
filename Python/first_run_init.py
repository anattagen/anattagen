"""
First-run initialization module.
Handles auto-detection of game directories, applications, and profile creation.
"""
import os
import shutil
import string
import logging
from pathlib import Path
from Python.models import AppConfig
from Python import constants

# Directories to search for in drive roots
GAME_DIRECTORY_NAMES = [
    "Games", "GOG Games", "Gaemz", "vidya", "Gaymez", 
    "Gaymes", "Installed Games", "Game Library"
]

# Controller mapper info
ANTIMICROX_EXES = ["antimicrox.exe", "antimicrox"]
KEYSTICKS_EXES = ["keysticks.exe"]

# Other tool executables
MULTIMONITOR_EXES = ["multimonitortool.exe"]
BORDERLESS_EXES = ["borderless-gaming-portable.exe"]


def get_available_drives():
    """Get list of available drive letters on Windows."""
    drives = []
    for letter in string.ascii_uppercase:
        drive = f"{letter}:\\"
        if os.path.exists(drive):
            drives.append(drive)
    return drives


def scan_for_game_directories():
    """
    Scan all drives for known game directory names in drive roots.
    Returns list of found directories.
    """
    found_dirs = []
    drives = get_available_drives()
    
    for drive in drives:
        for dir_name in GAME_DIRECTORY_NAMES:
            dir_path = os.path.join(drive, dir_name)
            if os.path.isdir(dir_path):
                found_dirs.append(dir_path)
                logging.info(f"Found game directory: {dir_path}")
    
    return found_dirs


def find_or_create_profiles_launchers_dirs():
    """
    Find existing Profiles/Launchers directories or create them.
    Search order: home dir, documents dir, project dir.
    If not found, create in project dir.
    Returns tuple: (profiles_dir, launchers_dir)
    """
    home_dir = Path.home()
    documents_dir = home_dir / "Documents"
    project_dir = Path(constants.APP_ROOT_DIR)
    
    search_locations = [home_dir, documents_dir, project_dir]
    
    profiles_dir = None
    launchers_dir = None
    
    # Search for existing directories
    for location in search_locations:
        if profiles_dir is None:
            candidate = location / "Profiles"
            if candidate.is_dir():
                profiles_dir = str(candidate)
                logging.info(f"Found Profiles directory: {profiles_dir}")
        
        if launchers_dir is None:
            candidate = location / "Launchers"
            if candidate.is_dir():
                launchers_dir = str(candidate)
                logging.info(f"Found Launchers directory: {launchers_dir}")
    
    # Create in project dir if not found
    if profiles_dir is None:
        profiles_dir = str(project_dir / "Profiles")
        os.makedirs(profiles_dir, exist_ok=True)
        logging.info(f"Created Profiles directory: {profiles_dir}")
    
    if launchers_dir is None:
        launchers_dir = str(project_dir / "Launchers")
        os.makedirs(launchers_dir, exist_ok=True)
        logging.info(f"Created Launchers directory: {launchers_dir}")
    
    return profiles_dir, launchers_dir


def find_executable_recursive(search_dir, exe_names):
    """
    Recursively search for an executable in a directory.
    Returns the path if found, None otherwise.
    """
    search_path = Path(search_dir)
    if not search_path.exists():
        return None
    
    for exe_name in exe_names:
        # Search recursively
        for found in search_path.rglob(exe_name):
            if found.is_file():
                logging.info(f"Found executable: {found}")
                return str(found)
    
    return None


def find_file_recursive(search_dir, filename):
    """
    Recursively search for a file in a directory.
    Returns the path if found, None otherwise.
    """
    search_path = Path(search_dir)
    if not search_path.exists():
        return None
    
    for found in search_path.rglob(filename):
        if found.is_file():
            return str(found)
    
    return None


def find_file_in_locations(filename, locations):
    """
    Search for a file in multiple locations (non-recursive).
    Returns the path if found, None otherwise.
    """
    for location in locations:
        candidate = Path(location) / filename
        if candidate.is_file():
            return str(candidate)
    return None


def copy_template_to_profile(template_path, output_path):
    """Copy a template file to create a profile."""
    try:
        if os.path.exists(template_path):
            shutil.copy2(template_path, output_path)
            logging.info(f"Created profile from template: {output_path}")
            return True
        else:
            logging.warning(f"Template not found: {template_path}")
            return False
    except Exception as e:
        logging.error(f"Error copying template: {e}")
        return False


def detect_controller_mapper(config: AppConfig):
    """
    Detect controller mapper (AntimicroX or Keysticks) and associated profiles.
    Prioritizes AntimicroX over Keysticks.
    """
    project_dir = Path(constants.APP_ROOT_DIR)
    bin_dir = project_dir / "bin"
    python_dir = project_dir / "Python"
    
    search_locations = [str(project_dir), str(bin_dir)]
    
    # Try to find AntimicroX first
    antimicrox_path = find_executable_recursive(bin_dir, ANTIMICROX_EXES)
    if antimicrox_path is None:
        antimicrox_path = find_executable_recursive(project_dir, ANTIMICROX_EXES)
    
    if antimicrox_path:
        config.controller_mapper_path = antimicrox_path
        logging.info(f"Using AntimicroX: {antimicrox_path}")
        
        # Look for AntimicroX profiles (.amgp)
        _setup_antimicrox_profiles(config, project_dir, bin_dir, python_dir, search_locations)
        return
    
    # Fall back to Keysticks
    keysticks_path = find_executable_recursive(bin_dir, KEYSTICKS_EXES)
    if keysticks_path is None:
        keysticks_path = find_executable_recursive(project_dir, KEYSTICKS_EXES)
    
    if keysticks_path:
        config.controller_mapper_path = keysticks_path
        logging.info(f"Using Keysticks: {keysticks_path}")
        
        # Look for Keysticks profiles (.ks)
        _setup_keysticks_profiles(config, project_dir, bin_dir, python_dir, search_locations)


def _setup_antimicrox_profiles(config, project_dir, bin_dir, python_dir, search_locations):
    """Set up AntimicroX profiles (.amgp files)."""
    
    # Search for Player1.amgp
    p1_profile = find_file_in_locations("Player1.amgp", search_locations)
    if p1_profile is None:
        p1_profile = find_file_recursive(bin_dir, "Player1.amgp")
    
    if p1_profile:
        config.p1_profile_path = p1_profile
    else:
        # Create from template
        output = project_dir / "Player1.amgp"
        if copy_template_to_profile(constants.AX_GAME_TEMPLATE_PATH, str(output)):
            config.p1_profile_path = str(output)
    
    # Search for Player2.amgp
    p2_profile = find_file_in_locations("Player2.amgp", search_locations)
    if p2_profile is None:
        p2_profile = find_file_recursive(bin_dir, "Player2.amgp")
    
    if p2_profile:
        config.p2_profile_path = p2_profile
    else:
        # Create from template (same as Player1 template)
        output = project_dir / "Player2.amgp"
        if copy_template_to_profile(constants.AX_GAME_TEMPLATE_PATH, str(output)):
            config.p2_profile_path = str(output)
    
    # Search for MediaCenter.amgp
    mc_profile = find_file_in_locations("MediaCenter.amgp", search_locations)
    if mc_profile is None:
        mc_profile = find_file_recursive(bin_dir, "MediaCenter.amgp")
    
    if mc_profile:
        config.mediacenter_profile_path = mc_profile
    else:
        # Create from desktop template
        output = project_dir / "MediaCenter.amgp"
        if copy_template_to_profile(constants.AX_DESK_TEMPLATE_PATH, str(output)):
            config.mediacenter_profile_path = str(output)


def _setup_keysticks_profiles(config, project_dir, bin_dir, python_dir, search_locations):
    """Set up Keysticks profiles (.ks files)."""
    
    # Search for Player1.ks
    p1_profile = find_file_in_locations("Player1.ks", search_locations)
    if p1_profile is None:
        p1_profile = find_file_recursive(bin_dir, "Player1.ks")
    
    if p1_profile:
        config.p1_profile_path = p1_profile
    else:
        # Create from template
        output = project_dir / "Player1.ks"
        if copy_template_to_profile(constants.KS_GAME_TEMPLATE_PATH, str(output)):
            config.p1_profile_path = str(output)
    
    # Search for Player2.ks
    p2_profile = find_file_in_locations("Player2.ks", search_locations)
    if p2_profile is None:
        p2_profile = find_file_recursive(bin_dir, "Player2.ks")
    
    if p2_profile:
        config.p2_profile_path = p2_profile
    else:
        # Create from template
        output = project_dir / "Player2.ks"
        if copy_template_to_profile(constants.KS_GAME_TEMPLATE_PATH, str(output)):
            config.p2_profile_path = str(output)
    
    # Search for MediaCenter.ks
    mc_profile = find_file_in_locations("MediaCenter.ks", search_locations)
    if mc_profile is None:
        mc_profile = find_file_recursive(bin_dir, "MediaCenter.ks")
    
    if mc_profile:
        config.mediacenter_profile_path = mc_profile
    else:
        # Create from desktop template
        output = project_dir / "MediaCenter.ks"
        if copy_template_to_profile(constants.KS_DESK_TEMPLATE_PATH, str(output)):
            config.mediacenter_profile_path = str(output)


def detect_multimonitor_tool(config: AppConfig):
    """Detect MultiMonitorTool and associated config files."""
    project_dir = Path(constants.APP_ROOT_DIR)
    bin_dir = project_dir / "bin"
    
    search_locations = [str(project_dir), str(bin_dir)]
    
    # Find executable
    mm_path = find_executable_recursive(bin_dir, MULTIMONITOR_EXES)
    if mm_path is None:
        mm_path = find_executable_recursive(project_dir, MULTIMONITOR_EXES)
    
    if mm_path:
        config.multi_monitor_tool_path = mm_path
        logging.info(f"Found MultiMonitorTool: {mm_path}")
    
    # Look for Desktop config (MM Media Config)
    for ext in [".xml", ".mon"]:
        desktop_config = find_file_in_locations(f"Desktop{ext}", search_locations)
        if desktop_config is None:
            desktop_config = find_file_recursive(bin_dir, f"Desktop{ext}")
        if desktop_config:
            config.multimonitor_media_path = desktop_config
            logging.info(f"Found MM Media Config: {desktop_config}")
            break
    
    # Look for Gaming config (MM Gaming Config)
    for ext in [".xml", ".mon"]:
        gaming_config = find_file_in_locations(f"Gaming{ext}", search_locations)
        if gaming_config is None:
            gaming_config = find_file_recursive(bin_dir, f"Gaming{ext}")
        if gaming_config:
            config.multimonitor_gaming_path = gaming_config
            logging.info(f"Found MM Gaming Config: {gaming_config}")
            break


def detect_borderless_gaming(config: AppConfig):
    """Detect Borderless Gaming application."""
    project_dir = Path(constants.APP_ROOT_DIR)
    bin_dir = project_dir / "bin"
    
    # Find executable
    bg_path = find_executable_recursive(bin_dir, BORDERLESS_EXES)
    if bg_path is None:
        bg_path = find_executable_recursive(project_dir, BORDERLESS_EXES)
    
    if bg_path:
        config.borderless_gaming_path = bg_path
        logging.info(f"Found Borderless Gaming: {bg_path}")


def run_first_time_setup(config: AppConfig):
    """
    Run the complete first-time setup.
    Called when no config.ini exists.
    """
    logging.info("Running first-time setup...")
    
    # 1. Scan for game directories
    game_dirs = scan_for_game_directories()
    config.source_dirs = game_dirs
    
    # 2. Find or create Profiles/Launchers directories
    profiles_dir, launchers_dir = find_or_create_profiles_launchers_dirs()
    config.profiles_dir = profiles_dir
    config.launchers_dir = launchers_dir
    
    # 3. Detect controller mapper and profiles
    detect_controller_mapper(config)
    
    # 4. Detect MultiMonitorTool
    detect_multimonitor_tool(config)
    
    # 5. Detect Borderless Gaming
    detect_borderless_gaming(config)
    
    # 6. Set default sequences
    config.launch_sequence = ["Controller-Mapper", "Monitor-Config", "No-TB", "Pre1", "Pre2", "Pre3", "Borderless"]
    config.exit_sequence = ["Post1", "Post2", "Post3", "Monitor-Config", "Taskbar", "Controller-Mapper"]
    
    logging.info("First-time setup complete.")


def is_first_run():
    """Check if this is the first run (no config file exists)."""
    config_ini = Path(constants.APP_ROOT_DIR) / "config.ini"
    return not config_ini.exists()
