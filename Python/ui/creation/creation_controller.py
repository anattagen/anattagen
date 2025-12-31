import configparser
import os
from pathlib import Path
import shutil
import logging
import requests
import json
import subprocess

from Python import constants
from Python.ui.name_utils import make_safe_filename

class CreationController:
    """
    Handles the creation of launcher files, shortcuts, and Game.ini configurations.
    """
    def __init__(self, main_window):
        self.main_window = main_window

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
        launcher_executable_path = launcher_base_dir / f"{safe_game_name}.bat"
        
        try:
            # Check overwrite flag for launcher directory
            if launcher_executable_path.exists() and not app_config.overwrite_states.get('launchers_dir', True): # Launcher dir overwrite is still global
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

            # 4. Create the launcher executable (conceptual step)
            # In a real build, you'd copy a pre-compiled Launcher.exe.
            # Here, we create a batch file as a functional placeholder.
            launcher_script_path = Path(constants.APP_ROOT_DIR) / "Python" / "Launcher.py"

            with open(launcher_executable_path, "w") as f:
                f.write(f'@echo off\npython "{launcher_script_path}" "{ini_path}"')

            # 5. Handle CEN/LC file propagation (copying profiles)
            self._propagate_files(game_data, game_profile_dir)

            # 6. Create the shortcut (.lnk) to the launcher executable
            # This step would use a library like `pylnk3` or cái `Shortcut.exe` tool.
            # For now, we are creating the files the shortcut would point to.
            
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
        config.set('Paths', 'ControllerMapperApp', game_data.get('controller_mapper_path', ''))
        config.set('Paths', 'BorderlessWindowingApp', game_data.get('borderless_windowing_path', ''))
        config.set('Paths', 'MultiMonitorTool', game_data.get('multi_monitor_app_path', ''))
        
        # Add Options/Arguments for Paths
        config.set('Paths', 'ControllerMapperOptions', app_config.controller_mapper_path_options)
        config.set('Paths', 'ControllerMapperArguments', app_config.controller_mapper_path_arguments)
        config.set('Paths', 'BorderlessWindowingOptions', app_config.borderless_gaming_path_options)
        config.set('Paths', 'BorderlessWindowingArguments', app_config.borderless_gaming_path_arguments)
        config.set('Paths', 'MultiMonitorOptions', app_config.multi_monitor_tool_path_options)
        config.set('Paths', 'MultiMonitorArguments', app_config.multi_monitor_tool_path_arguments)
        
        # Handle profile paths with CEN/LC logic
        config.set('Paths', 'Player1Profile', self._get_profile_path('player1_profile', game_data))
        config.set('Paths', 'Player2Profile', self._get_profile_path('player2_profile', game_data))
        config.set('Paths', 'MultiMonitorGamingConfig', self._get_profile_path('mm_game_profile', game_data))
        config.set('Paths', 'MultiMonitorDesktopConfig', self._get_profile_path('mm_desktop_profile', game_data))
        
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
        config.set('PreLaunch', 'App1', game_data.get('pre1_path', '').lstrip('<> '))
        config.set('PreLaunch', 'App1Options', app_config.pre1_path_options)
        config.set('PreLaunch', 'App1Arguments', app_config.pre1_path_arguments)
        config.set('PreLaunch', 'App1Wait', str(game_data.get('pre_1_run_wait', False)))
        
        config.set('PreLaunch', 'App2', game_data.get('pre2_path', '').lstrip('<> '))
        config.set('PreLaunch', 'App2Options', app_config.pre2_path_options)
        config.set('PreLaunch', 'App2Arguments', app_config.pre2_path_arguments)
        config.set('PreLaunch', 'App2Wait', str(game_data.get('pre_2_run_wait', False)))
        
        config.set('PreLaunch', 'App3', game_data.get('pre3_path', '').lstrip('<> '))
        config.set('PreLaunch', 'App3Options', app_config.pre3_path_options)
        config.set('PreLaunch', 'App3Arguments', app_config.pre3_path_arguments)
        config.set('PreLaunch', 'App3Wait', str(game_data.get('pre_3_run_wait', False)))

        config.add_section('PostLaunch')
        config.set('PostLaunch', 'App1', game_data.get('post1_path', '').lstrip('<> '))
        config.set('PostLaunch', 'App1Options', app_config.post1_path_options)
        config.set('PostLaunch', 'App1Arguments', app_config.post1_path_arguments)
        config.set('PostLaunch', 'App1Wait', str(game_data.get('post_1_run_wait', False)))
        
        config.set('PostLaunch', 'App2', game_data.get('post2_path', '').lstrip('<> '))
        config.set('PostLaunch', 'App2Options', app_config.post2_path_options)
        config.set('PostLaunch', 'App2Arguments', app_config.post2_path_arguments)
        config.set('PostLaunch', 'App2Wait', str(game_data.get('post_2_run_wait', False)))
        
        config.set('PostLaunch', 'App3', game_data.get('post3_path', '').lstrip('<> '))
        config.set('PostLaunch', 'App3Options', app_config.post3_path_options)
        config.set('PostLaunch', 'App3Arguments', app_config.post3_path_arguments)
        config.set('PostLaunch', 'App3Wait', str(game_data.get('post_3_run_wait', False)))
        
        config.set('PostLaunch', 'JustAfterLaunchApp', game_data.get('just_after_launch_path', '').lstrip('<> '))
        config.set('PostLaunch', 'JustAfterLaunchOptions', app_config.just_after_launch_path_options)
        config.set('PostLaunch', 'JustAfterLaunchArguments', app_config.just_after_launch_path_arguments)
        config.set('PostLaunch', 'JustAfterLaunchWait', str(game_data.get('just_after_launch_run_wait', False)))
        
        config.set('PostLaunch', 'JustBeforeExitApp', game_data.get('just_before_exit_path', '').lstrip('<> '))
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

    def _get_profile_path(self, profile_key, game_data):
        """
        Determines the correct path for a profile based on CEN/LC mode from the editor data.
        Enforces centralized path behavior to prevent profile folders in Launchers directory.
        """
        path_with_mode = game_data.get(profile_key, "")
        original_path = path_with_mode[2:] if len(path_with_mode) > 1 else ""
        
        # Always return the original path (Centralized behavior)
        return original_path

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