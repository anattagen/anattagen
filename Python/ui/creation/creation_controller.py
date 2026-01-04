import configparser
import os
from pathlib import Path
import shutil
import logging
import requests
import json
import subprocess
import zipfile

from Python import constants
from Python.ui.name_utils import make_safe_filename

class CreationController:
    """
    Handles the creation of launcher files, shortcuts, and Game.ini configurations.
    """
    def __init__(self, main_window):
        self.main_window = main_window
        self.repo_tools = self._parse_repos_set()

    def create_all(self, selected_games):
        """
        Processes all selected games from the editor tab to create their launchers.
        """
        processed_count = 0
        failed_count = 0

        for game_data in selected_games:
            if self._create_for_single_game(game_data):
                processed_count += 1
            else:
                failed_count += 1
        
        return {"processed_count": processed_count, "failed_count": failed_count}

    def _create_for_single_game(self, game_data):
        """
        Creates the necessary files and folders for a single game.
        """
        app_config = self.main_window.config
        game_name_override = game_data.get('name_override', 'New Game')
        safe_game_name = make_safe_filename(game_name_override)
        
        # Check if launcher creation is enabled in Setup Tab
        if not app_config.defaults.get('launchers_dir_enabled', True):
            logging.info(f"Skipping launcher creation for {game_name_override} (Disabled in Setup)")
            return True

        # 1. Define the launcher directory for this game
        launcher_base_dir = Path(app_config.launchers_dir)
        launcher_shortcut_path = launcher_base_dir / f"{safe_game_name}.lnk"
        
        try:
            # Check overwrite flag for launcher directory
            if launcher_shortcut_path.exists() and not app_config.overwrite_states.get('launchers_dir', True): # Launcher dir overwrite is still global
                logging.info(f"Skipping launcher creation for {game_name_override} (Overwrite disabled)")
                return True

            # 2. Create the directory structure
            launcher_base_dir.mkdir(parents=True, exist_ok=True)
            
            # 2a. Create Profile Directory in the correct location (Profiles folder)
            profiles_base_dir = Path(app_config.profiles_dir)
            game_profile_dir = profiles_base_dir / safe_game_name

            if app_config.defaults.get('profiles_dir_enabled', True):
                try:
                    game_profile_dir.mkdir(parents=True, exist_ok=True)
                    (game_profile_dir / "Saves").mkdir(exist_ok=True)
                except Exception as e:
                    logging.error(f"Failed to create profile directory for {game_name_override}: {e}")

            # 3. Create the Game.ini file
            ini_path = game_profile_dir / "Game.ini"
            self._create_game_ini(ini_path, game_data, app_config, game_profile_dir)
            
            # 3b. Download Game.json if enabled
            if app_config.download_game_json:
                self._download_game_json(game_data, game_profile_dir)

            # 5. Handle CEN/LC file propagation (copying profiles)
            self._propagate_files(game_data, game_profile_dir)
            self._propagate_apps(game_data, game_profile_dir)

            # 6. Create Profile Shortcut (pointing to source title's executable)
            game_exe_path = Path(game_data.get('directory', '')) / game_data.get('name', '')
            profile_shortcut_path = game_profile_dir / f"{safe_game_name}.lnk"
            
            self._create_shortcut(
                target_path=game_exe_path,
                shortcut_path=profile_shortcut_path,
                working_dir=game_data.get('directory', ''),
                description=f"Shortcut to {game_name_override}"
            )

            # 7. Create Launcher Shortcut (pointing to Launcher.exe)
            self._create_shortcut(
                target_path=constants.LAUNCHER_EXECUTABLE,
                shortcut_path=launcher_shortcut_path,
                arguments=f'"{profile_shortcut_path}"',
                working_dir=game_data.get('directory', ''),
                icon_path=game_exe_path,
                description=f"Launch {game_name_override}"
            )

            self.main_window.statusBar().showMessage(f"Successfully created launcher for {game_name_override}", 3000)
            return True
            
        except Exception as e:
            logging.error(f"Failed to create launcher for {game_name_override}: {e}", exc_info=True)
            self.main_window.statusBar().showMessage(f"Error creating launcher for {game_name_override}: {e}", 5000)
            return False

    def _create_shortcut(self, target_path, shortcut_path, arguments="", working_dir="", icon_path=None, description=""):
        """Creates a Windows shortcut using the bundled Shortcut.exe."""
        shortcut_exe = os.path.join(constants.APP_ROOT_DIR, "bin", "Shortcut.exe")
        if not os.path.exists(shortcut_exe):
            logging.error(f"Shortcut.exe not found at {shortcut_exe}")
            return False

        cmd = [
            shortcut_exe,
            "/F:" + str(shortcut_path),
            "/A:C",
            "/T:" + str(target_path)
        ]
        if arguments:
            cmd.append("/P:" + str(arguments))
        if working_dir:
            cmd.append("/W:" + str(working_dir))
        if icon_path:
            cmd.append("/I:" + str(icon_path))
        if description:
            cmd.append("/D:" + str(description))

        subprocess.run(cmd, check=True, capture_output=True)

    def _download_game_json(self, game_data, game_launcher_dir):
        """Downloads Game.json from Steam API if steam_id is present."""
        steam_id = game_data.get('steam_id')
        if not steam_id or steam_id == 'NOT_FOUND_IN_DATA' or steam_id == 'ITEM_IS_NONE':
            logging.info(f"Skipping Game.json download: No valid Steam ID for {game_data.get('name_override')}")
            return

        url = f"https://store.steampowered.com/api/appdetails?appids={steam_id}"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            json_path = game_launcher_dir / "Game.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            logging.info(f"Downloaded Game.json for {game_data.get('name_override')} (AppID: {steam_id})")
        except Exception as e:
            logging.error(f"Failed to download Game.json for {game_data.get('name_override')} (AppID: {steam_id}): {e}")

    def _create_game_ini(self, ini_path, game_data, app_config, game_launcher_dir):
        """
        Generates and saves the Game.ini file based on game-specific and global settings.
        """
        config = configparser.ConfigParser()

        # --- [Game] Section ---
        config.add_section('Game')
        config.set('Game', 'Executable', game_data.get('name', ''))
        config.set('Game', 'Directory', game_data.get('directory', ''))
        config.set('Game', 'Name', game_data.get('name_override', ''))

        # --- [Paths] Section ---
        config.add_section('Paths')
        config.set('Paths', 'ControllerMapperApp', self._get_app_path_for_ini('controller_mapper_path', game_data, game_profile_dir))
        config.set('Paths', 'BorderlessWindowingApp', self._get_app_path_for_ini('borderless_windowing_path', game_data, game_profile_dir))
        config.set('Paths', 'MultiMonitorTool', self._get_app_path_for_ini('multi_monitor_app_path', game_data, game_profile_dir))
        
        # Add Options/Arguments for Paths
        config.set('Paths', 'ControllerMapperOptions', app_config.controller_mapper_path_options)
        config.set('Paths', 'ControllerMapperArguments', app_config.controller_mapper_path_arguments)
        config.set('Paths', 'BorderlessWindowingOptions', app_config.borderless_gaming_path_options)
        config.set('Paths', 'BorderlessWindowingArguments', app_config.borderless_gaming_path_arguments)
        config.set('Paths', 'MultiMonitorOptions', app_config.multi_monitor_tool_path_options)
        config.set('Paths', 'MultiMonitorArguments', app_config.multi_monitor_tool_path_arguments)
        
        # Handle profile paths with CEN/LC logic
        config.set('Paths', 'Player1Profile', self._get_profile_path('player1_profile', game_data, game_profile_dir))
        config.set('Paths', 'Player2Profile', self._get_profile_path('player2_profile', game_data, game_profile_dir))
        config.set('Paths', 'MultiMonitorGamingConfig', self._get_profile_path('mm_game_profile', game_data, game_profile_dir))
        config.set('Paths', 'MultiMonitorDesktopConfig', self._get_profile_path('mm_desktop_profile', game_data, game_profile_dir))
        
        # --- [Options] Section ---
        config.add_section('Options')
        config.set('Options', 'RunAsAdmin', str(game_data.get('run_as_admin', False)))
        config.set('Options', 'HideTaskbar', str(game_data.get('hide_taskbar', False)))
        config.set('Options', 'Borderless', game_data.get('options', '0'))
        config.set('Options', 'UseKillList', str(game_data.get('kill_list_enabled', False)))
        config.set('Options', 'TerminateBorderlessOnExit', str(game_data.get('terminate_borderless_on_exit', app_config.terminate_borderless_on_exit)))
        config.set('Options', 'KillList', game_data.get('kill_list', ''))
        # --- [PreLaunch] & [PostLaunch] Sections ---
        config.add_section('PreLaunch')
        config.set('PreLaunch', 'App1', self._get_app_path_for_ini('pre1_path', game_data, game_profile_dir))
        config.set('PreLaunch', 'App1Options', app_config.pre1_path_options)
        config.set('PreLaunch', 'App1Arguments', app_config.pre1_path_arguments)
        config.set('PreLaunch', 'App1Wait', str(game_data.get('pre_1_run_wait', False)))
        
        config.set('PreLaunch', 'App2', self._get_app_path_for_ini('pre2_path', game_data, game_profile_dir))
        config.set('PreLaunch', 'App2Options', app_config.pre2_path_options)
        config.set('PreLaunch', 'App2Arguments', app_config.pre2_path_arguments)
        config.set('PreLaunch', 'App2Wait', str(game_data.get('pre_2_run_wait', False)))
        
        config.set('PreLaunch', 'App3', self._get_app_path_for_ini('pre3_path', game_data, game_profile_dir))
        config.set('PreLaunch', 'App3Options', app_config.pre3_path_options)
        config.set('PreLaunch', 'App3Arguments', app_config.pre3_path_arguments)
        config.set('PreLaunch', 'App3Wait', str(game_data.get('pre_3_run_wait', False)))

        config.add_section('PostLaunch')
        config.set('PostLaunch', 'App1', self._get_app_path_for_ini('post1_path', game_data, game_profile_dir))
        config.set('PostLaunch', 'App1Options', app_config.post1_path_options)
        config.set('PostLaunch', 'App1Arguments', app_config.post1_path_arguments)
        config.set('PostLaunch', 'App1Wait', str(game_data.get('post_1_run_wait', False)))
        
        config.set('PostLaunch', 'App2', self._get_app_path_for_ini('post2_path', game_data, game_profile_dir))
        config.set('PostLaunch', 'App2Options', app_config.post2_path_options)
        config.set('PostLaunch', 'App2Arguments', app_config.post2_path_arguments)
        config.set('PostLaunch', 'App2Wait', str(game_data.get('post_2_run_wait', False)))
        
        config.set('PostLaunch', 'App3', self._get_app_path_for_ini('post3_path', game_data, game_profile_dir))
        config.set('PostLaunch', 'App3Options', app_config.post3_path_options)
        config.set('PostLaunch', 'App3Arguments', app_config.post3_path_arguments)
        config.set('PostLaunch', 'App3Wait', str(game_data.get('post_3_run_wait', False)))
        
        config.set('PostLaunch', 'JustAfterLaunchApp', self._get_app_path_for_ini('just_after_launch_path', game_data, game_profile_dir))
        config.set('PostLaunch', 'JustAfterLaunchOptions', app_config.just_after_launch_path_options)
        config.set('PostLaunch', 'JustAfterLaunchArguments', app_config.just_after_launch_path_arguments)
        config.set('PostLaunch', 'JustAfterLaunchWait', str(game_data.get('just_after_launch_run_wait', False)))
        
        config.set('PostLaunch', 'JustBeforeExitApp', self._get_app_path_for_ini('just_before_exit_path', game_data, game_profile_dir))
        config.set('PostLaunch', 'JustBeforeExitOptions', app_config.just_before_exit_path_options)
        config.set('PostLaunch', 'JustBeforeExitArguments', app_config.just_before_exit_path_arguments)
        config.set('PostLaunch', 'JustBeforeExitWait', str(game_data.get('just_before_exit_run_wait', False)))

        # --- [Sequences] Section ---
        config.add_section('Sequences')
        config.set('Sequences', 'LaunchSequence', ",".join(app_config.launch_sequence))
        config.set('Sequences', 'ExitSequence', ",".join(app_config.exit_sequence))

        # Write the INI file
        with open(ini_path, 'w', encoding='utf-8') as configfile:
            config.write(configfile)

    def _get_profile_path(self, profile_key, game_data, game_profile_dir=None):
        """
        Determines the correct path for a profile based on CEN/LC mode from the editor data.
        Enforces centralized path behavior to prevent profile folders in Launchers directory.
        """
        path_with_mode = game_data.get(profile_key, "")
        if not path_with_mode:
            return ""
        
        mode = path_with_mode[0] if len(path_with_mode) > 0 else '<'
        original_path = path_with_mode[2:] if len(path_with_mode) > 1 else ""
        
        if mode == '>': # LC (Launch Conditional / Local Copy)
            # Return absolute path to the file in the profile directory
            if game_profile_dir:
                return str(Path(game_profile_dir) / os.path.basename(original_path))
            return os.path.basename(original_path)
        
        # CEN (Centralized)
        return original_path

    def _get_app_path_for_ini(self, key, game_data, target_dir):
        """
        Determines the correct path for an app/script based on CEN/LC mode.
        If LC, returns the relative path to the file in the profile directory.
        """
        path_val = game_data.get(key, "")
        if not path_val:
            return ""
            
        if path_val.startswith('>'):
            # LC mode
            original_path = path_val[2:].strip()
            exe_name = os.path.basename(original_path)
            
            # Try to find it in target_dir (it might be in a subfolder if extracted)
            found = self._find_file_recursive(target_dir, exe_name)
            if found:
                try:
                    return str(Path(found).relative_to(target_dir))
                except ValueError:
                    return exe_name
            return exe_name
        else:
            # CEN mode
            return path_val.lstrip('<> ')

    def _propagate_apps(self, game_data, target_dir):
        """
        Handles LC propagation for applications and scripts.
        Downloads/Extracts if supported in repos.set, otherwise copies.
        """
        app_keys = [
            'controller_mapper_path', 'borderless_windowing_path', 'multi_monitor_app_path',
            'just_after_launch_path', 'just_before_exit_path',
            'pre1_path', 'pre2_path', 'pre3_path',
            'post1_path', 'post2_path', 'post3_path'
        ]

        for key in app_keys:
            path_val = game_data.get(key, "")
            if not path_val or not path_val.startswith('>'):
                continue

            # It is LC
            original_path = path_val[2:].strip()
            if not original_path:
                continue

            exe_name = os.path.basename(original_path)
            exe_lower = exe_name.lower()

            # Check if it's a supported repo tool
            if exe_lower in self.repo_tools:
                url = self.repo_tools[exe_lower]
                # Check if already exists in target_dir (recursively)
                if self._find_file_recursive(target_dir, exe_name):
                    logging.info(f"Tool {exe_name} already present in {target_dir}, skipping download.")
                    continue
                
                # Download and extract
                try:
                    logging.info(f"Downloading {exe_name} from {url}...")
                    response = requests.get(url, stream=True)
                    response.raise_for_status()
                    
                    zip_path = target_dir / f"{exe_name}.zip"
                    with open(zip_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    logging.info(f"Extracting {exe_name}...")
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(target_dir)
                    
                    os.remove(zip_path)
                except Exception as e:
                    logging.error(f"Failed to download/extract {exe_name}: {e}")
            else:
                # Not a repo tool, just copy the file
                src_path = Path(original_path)
                if src_path.exists():
                    dest_path = target_dir / src_path.name
                    if not dest_path.exists() or self.main_window.config.overwrite_states.get(key, True):
                        try:
                            shutil.copy2(src_path, dest_path)
                            logging.info(f"Copied {src_path} to {dest_path}")
                        except Exception as e:
                            logging.error(f"Failed to copy {src_path}: {e}")

    def _find_file_recursive(self, root_dir, filename):
        """Recursively find a file in a directory."""
        for root, dirs, files in os.walk(root_dir):
            if filename in files:
                return os.path.join(root, filename)
        return None

    def _propagate_files(self, game_data, target_dir):
        """
        Copies files to the target directory (Profiles folder) if they are set to LC mode.
        """
        app_config = self.main_window.config
        
        # Map profile keys to their overwrite config keys
        profile_map = {
            'player1_profile': 'p1_profile_path',
            'player2_profile': 'p2_profile_path',
            'mm_game_profile': 'multimonitor_gaming_path',
            'mm_desktop_profile': 'multimonitor_media_path'
        }

        for key, config_key in profile_map.items():
            path_with_mode = game_data.get(key, "")
            if not path_with_mode:
                continue
                
            mode = path_with_mode[0] if len(path_with_mode) > 0 else '<'
            original_path_str = path_with_mode[2:] if len(path_with_mode) > 1 else ""

            # Only copy if mode is LC (>) and path exists
            if mode == '>' and original_path_str and os.path.exists(original_path_str):
                original_path = Path(original_path_str)
                target_file = target_dir / original_path.name
                
                if target_file.exists() and not app_config.overwrite_states.get(config_key, True):
                    continue

                try:
                    shutil.copy2(original_path, target_file)
                    logging.info(f"Copied profile {original_path} to {target_file}")
                except Exception as e:
                    logging.error(f"Failed to copy profile {original_path} to {target_dir}: {e}")

    def _parse_repos_set(self):
        """Parses the repos.set file to get tool download URLs."""
        repos = {}
        if not os.path.exists(constants.REPOS_SET):
            return repos

        config = configparser.ConfigParser()
        config.read(constants.REPOS_SET)

        global_vars = {}
        if "GLOBAL" in config:
            global_vars = dict(config["GLOBAL"])
            global_vars["app_directory"] = constants.APP_ROOT_DIR

        # Map exe_name -> url
        tool_map = {}

        for section in config.sections():
            if section == "GLOBAL": continue
            for key, value in config[section].items():
                # Substitute vars
                val = value
                for var_name, var_val in global_vars.items():
                    val = val.replace(f"${var_name.upper()}", var_val)
                    val = val.replace(f"${var_name}", var_val)
                val = val.replace("$ITEMNAME", key)
                
                parts = val.split('|')
                if len(parts) >= 3:
                    url = parts[0]
                    exe_name = parts[2].lower() # Normalize to lower for matching
                    tool_map[exe_name] = url
        return tool_map