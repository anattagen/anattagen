import os
import json
import logging
import shutil
import string
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal
from ..models import AppConfig
from .. import constants


CONFIG_FILE = os.path.join(constants.APP_ROOT_DIR, "config.json")

# --- First Run Constants ---
GAME_DIRECTORY_NAMES = [
    "Games", "GOG Games", "Gaemz", "vidya", "Gaymez",
    "Gaymes", "Installed Games", "Game Library"
]
ANTIMICROX_EXES = ["antimicrox.exe", "antimicrox"]
KEYSTICKS_EXES = ["keysticks.exe"]
MULTIMONITOR_EXES = ["multimonitortool.exe"]
BORDERLESS_EXES = ["borderlessgaming.exe"]


class ConfigManager(QObject):
    """Manages loading and saving of application configuration."""
    status_updated = pyqtSignal(str, int)

    def __init__(self):
        super().__init__()
        self.config_file = CONFIG_FILE

    def load_config(self) -> AppConfig:
        """Loads the application configuration from config.json."""
        if not os.path.exists(self.config_file):
            logging.info("Config file not found. Running first-time setup.")
            self.status_updated.emit("Performing first-time setup...", 0)
            config = self._first_run_setup()
            self.save_config(config)
            self.status_updated.emit("First-time setup complete.", 3000)
            return config

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Create an AppConfig instance and update it with loaded data
            config = AppConfig()
            for key, value in config_data.items():
                if hasattr(config, key):
                    setattr(config, key, value)

            self.status_updated.emit("Configuration loaded.", 3000)
            return config
        except Exception as e:
            logging.error(f"Failed to load config file {self.config_file}: {e}", exc_info=True)
            self.status_updated.emit(f"Failed to load config file: {e}", 5000)
            # Fallback to default config if loading fails
            return self._first_run_setup()

    def save_config(self, config: AppConfig):
        """Saves the application configuration to config.json."""
        try:
            # Use a dictionary representation of the AppConfig model
            config_data = {key: getattr(config, key) for key in dir(config) if not key.startswith('__') and not callable(getattr(config, key))}
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4)
            self.status_updated.emit("Configuration saved.", 3000)
            logging.info(f"Configuration saved to '{self.config_file}'.")
        except Exception as e:
            logging.error(f"Failed to save config file {self.config_file}: {e}", exc_info=True)
            self.status_updated.emit(f"Failed to save config file: {e}", 5000)

    def _first_run_setup(self) -> AppConfig:
        """
        Run the complete first-time setup.
        Called when no config.json exists.
        """
        logging.info("Running first-time setup...")
        config = AppConfig()

        config.source_dirs = self._scan_for_game_directories()
        config.profiles_dir, config.launchers_dir = self._find_or_create_profiles_launchers_dirs()
        self._detect_controller_mapper(config)
        self._detect_multimonitor_tool(config)
        self._detect_borderless_gaming(config)

        # Set default sequences
        config.launch_sequence = ["Controller-Mapper", "Monitor-Config", "No-TB", "Pre1", "Pre2", "Pre3", "Borderless"]
        config.exit_sequence = ["Post1", "Post2", "Post3", "Monitor-Config", "Taskbar", "Controller-Mapper"]

        # Set default enabled states
        config.defaults = {
            'controller_mapper_path_enabled': True,
            'borderless_gaming_path_enabled': True,
            'multi_monitor_tool_path_enabled': True,
            'just_after_launch_path_enabled': True,
            'just_before_exit_path_enabled': True,
            'pre1_path_enabled': True,
            'post1_path_enabled': True,
            'pre2_path_enabled': True,
            'post2_path_enabled': True,
            'pre3_path_enabled': True,
            'post3_path_enabled': True,
        }

        # Set default run-wait states
        config.run_wait_states = {
            'controller_mapper_path_run_wait': True,
            'borderless_gaming_path_run_wait': True,
            'multi_monitor_tool_path_run_wait': True,
            'just_after_launch_path_run_wait': False,
            'just_before_exit_path_run_wait': True,
            'pre1_path_run_wait': True, 'post1_path_run_wait': True,
            'pre2_path_run_wait': True, 'post2_path_run_wait': True,
            'pre3_path_run_wait': True, 'post3_path_run_wait': True,
        }

        # Set default overwrite states (Deployment Tab -> Creation)
        config.overwrite_states = {
            key: True for key in [
                "profiles_dir", "launchers_dir", "controller_mapper_path", "borderless_gaming_path",
                "multi_monitor_tool_path", "just_after_launch_path", "just_before_exit_path",
                "p1_profile_path", "p2_profile_path", "mediacenter_profile_path",
                "multimonitor_gaming_path", "multimonitor_media_path",
                "pre1_path", "pre2_path", "pre3_path", "post1_path", "post2_path", "post3_path"
            ]
        }

        # Set default deployment tab options
        config.download_game_json = False
        config.hide_taskbar = False
        config.run_as_admin = True
        config.enable_name_matching = True
        config.steam_json_version = 2
        config.create_overwrite_joystick_profiles = True

        logging.info("First-time setup complete.")
        return config

    def _get_available_drives(self):
        drives = []
        for letter in string.ascii_uppercase:
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                drives.append(drive)
        return drives

    def _scan_for_game_directories(self):
        found_dirs = []
        drives = self._get_available_drives()
        for drive in drives:
            for dir_name in GAME_DIRECTORY_NAMES:
                dir_path = os.path.join(drive, dir_name)
                if os.path.isdir(dir_path):
                    found_dirs.append(dir_path)
                    logging.info(f"Found game directory: {dir_path}")
        return found_dirs

    def _find_or_create_profiles_launchers_dirs(self):
        home_dir = Path.home()
        documents_dir = home_dir / "Documents"
        project_dir = Path(constants.APP_ROOT_DIR)
        search_locations = [home_dir, documents_dir, project_dir]
        profiles_dir, launchers_dir = None, None

        for location in search_locations:
            if profiles_dir is None and (location / "Profiles").is_dir():
                profiles_dir = str(location / "Profiles")
            if launchers_dir is None and (location / "Launchers").is_dir():
                launchers_dir = str(location / "Launchers")

        if profiles_dir is None:
            profiles_dir = str(project_dir / "Profiles")
            os.makedirs(profiles_dir, exist_ok=True)
        if launchers_dir is None:
            launchers_dir = str(project_dir / "Launchers")
            os.makedirs(launchers_dir, exist_ok=True)
        return profiles_dir, launchers_dir

    def _find_executable_recursive(self, search_dir, exe_names):
        search_path = Path(search_dir)
        if not search_path.exists(): return None
        for exe_name in exe_names:
            for found in search_path.rglob(exe_name):
                if found.is_file():
                    logging.info(f"Found executable: {found}")
                    return str(found)
        return None

    def _detect_controller_mapper(self, config: AppConfig):
        project_dir = Path(constants.APP_ROOT_DIR)
        bin_dir = project_dir / "bin"
        antimicrox_path = self._find_executable_recursive(bin_dir, ANTIMICROX_EXES) or self._find_executable_recursive(project_dir, ANTIMICROX_EXES)
        if antimicrox_path:
            config.controller_mapper_path = antimicrox_path
            logging.info(f"Using AntimicroX: {antimicrox_path}")
            return

        keysticks_path = self._find_executable_recursive(bin_dir, KEYSTICKS_EXES) or self._find_executable_recursive(project_dir, KEYSTICKS_EXES)
        if keysticks_path:
            config.controller_mapper_path = keysticks_path
            logging.info(f"Using Keysticks: {keysticks_path}")

    def _detect_multimonitor_tool(self, config: AppConfig):
        project_dir = Path(constants.APP_ROOT_DIR)
        bin_dir = project_dir / "bin"
        mm_path = self._find_executable_recursive(bin_dir, MULTIMONITOR_EXES) or self._find_executable_recursive(project_dir, MULTIMONITOR_EXES)
        if mm_path:
            config.multi_monitor_tool_path = mm_path
            logging.info(f"Found MultiMonitorTool: {mm_path}")

    def _detect_borderless_gaming(self, config: AppConfig):
        project_dir = Path(constants.APP_ROOT_DIR)
        bin_dir = project_dir / "bin"
        bg_path = self._find_executable_recursive(bin_dir, BORDERLESS_EXES) or self._find_executable_recursive(project_dir, BORDERLESS_EXES)
        if bg_path:
            config.borderless_gaming_path = bg_path
            logging.info(f"Found Borderless Gaming: {bg_path}")

    def reset_to_defaults(self, main_window):
        """Resets the configuration to defaults and re-syncs the UI."""
        logging.info("Resetting configuration to defaults.")
        # Create a new default config
        default_config = self._first_run_setup()
        # Save it
        self.save_config(default_config)
        # Update the main window's config instance
        main_window.config = default_config
        # Update the data manager with the new config, preserving the instance
        main_window.data_manager.config = default_config
        # Re-sync the entire UI
        main_window.sync_ui_from_config()
        self.status_updated.emit("Configuration has been reset to defaults.", 4000)