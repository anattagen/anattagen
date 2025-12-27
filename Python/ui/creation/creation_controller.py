import configparser
import os
from pathlib import Path
import shutil
import logging

from Python import constants

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
        
        # 1. Define the launcher directory for this game
        launcher_base_dir = Path(app_config.launchers_dir)
        game_launcher_dir = launcher_base_dir / game_name_override
        
        try:
            # 2. Create the directory structure
            game_launcher_dir.mkdir(parents=True, exist_ok=True)
            
            # 3. Create the Game.ini file
            ini_path = game_launcher_dir / "Game.ini"
            self._create_game_ini(ini_path, game_data, app_config, game_launcher_dir)
            
            # 4. Create the launcher executable (conceptual step)
            # In a real build, you'd copy a pre-compiled Launcher.exe.
            # Here, we create a batch file as a functional placeholder.
            launcher_script_path = Path(constants.APP_ROOT_DIR) / "Python" / "Launcher.py"
            shortcut_path = game_launcher_dir / f"{game_name_override}.lnk"
            launcher_executable_path = game_launcher_dir / f"{game_name_override}_launcher.bat"

            with open(launcher_executable_path, "w") as f:
                f.write(f'@echo off\npython "{launcher_script_path}" "{shortcut_path}"')

            # 5. Handle CEN/LC file propagation (copying profiles)
            self._propagate_files(game_data, game_launcher_dir)

            # 6. Create the shortcut (.lnk) to the launcher executable
            # This step would use a library like `pylnk3` or cái `Shortcut.exe` tool.
            # For now, we are creating the files the shortcut would point to.
            
            self.main_window.statusBar().showMessage(f"Successfully created launcher for {game_name_override}", 3000)
            return True
            
        except Exception as e:
            logging.error(f"Failed to create launcher for {game_name_override}: {e}", exc_info=True)
            self.main_window.statusBar().showMessage(f"Error creating launcher for {game_name_override}: {e}", 5000)
            return False

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
        config.set('Paths', 'ControllerMapperApp', app_config.controller_mapper_path)
        config.set('Paths', 'BorderlessWindowingApp', app_config.borderless_gaming_path)
        config.set('Paths', 'MultiMonitorTool', app_config.multi_monitor_tool_path)
        
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
        config.set('Options', 'UseKillList', str(app_config.use_kill_list))
        config.set('Options', 'TerminateBorderlessOnExit', str(app_config.terminate_borderless_on_exit))

        # --- [PreLaunch] & [PostLaunch] Sections ---
        config.add_section('PreLaunch')
        config.set('PreLaunch', 'App1', game_data.get('pre1_path', '').lstrip('<> '))
        config.set('PreLaunch', 'App1Wait', str(game_data.get('pre_1_run_wait', False)))
        config.set('PreLaunch', 'App2', game_data.get('pre2_path', '').lstrip('<> '))
        config.set('PreLaunch', 'App2Wait', str(game_data.get('pre_2_run_wait', False)))
        config.set('PreLaunch', 'App3', game_data.get('pre3_path', '').lstrip('<> '))
        config.set('PreLaunch', 'App3Wait', str(game_data.get('pre_3_run_wait', False)))

        config.add_section('PostLaunch')
        config.set('PostLaunch', 'App1', game_data.get('post1_path', '').lstrip('<> '))
        config.set('PostLaunch', 'App1Wait', str(game_data.get('post_1_run_wait', False)))
        config.set('PostLaunch', 'App2', game_data.get('post2_path', '').lstrip('<> '))
        config.set('PostLaunch', 'App2Wait', str(game_data.get('post_2_run_wait', False)))
        config.set('PostLaunch', 'App3', game_data.get('post3_path', '').lstrip('<> '))
        config.set('PostLaunch', 'App3Wait', str(game_data.get('post_3_run_wait', False)))
        config.set('PostLaunch', 'JustAfterLaunchApp', game_data.get('ja_path', '').lstrip('<> '))
        config.set('PostLaunch', 'JustAfterLaunchWait', str(game_data.get('ja_run_wait', False)))
        config.set('PostLaunch', 'JustBeforeExitApp', game_data.get('jb_path', '').lstrip('<> '))
        config.set('PostLaunch', 'JustBeforeExitWait', str(game_data.get('jb_run_wait', False)))

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
        """
        path_with_mode = game_data.get(profile_key, "")
        mode = path_with_mode[0] if path_with_mode else '<'
        original_path = path_with_mode[2:] if len(path_with_mode) > 1 else ""

        if mode == '<':  # CEN (Centralized)
            return original_path
        else:  # LC (Launch Conditional)
            if not original_path:
                return ""
            filename = os.path.basename(original_path)
            relative_path = Path("Profiles") / profile_key / filename
            return str(relative_path)

    def _propagate_files(self, game_data, game_launcher_dir):
        """
        Copies files to the game's launcher directory if they are set to LC mode.
        """
        profile_keys = [
            'player1_profile', 'player2_profile', 'mm_game_profile', 'mm_desktop_profile'
        ]

        for key in profile_keys:
            path_with_mode = game_data.get(key, "")
            mode = path_with_mode[0] if path_with_mode else '<'
            original_path_str = path_with_mode[2:] if len(path_with_mode) > 1 else ""

            if mode == '>' and original_path_str and os.path.exists(original_path_str):
                original_path = Path(original_path_str)
                target_dir = game_launcher_dir / "Profiles" / key
                target_dir.mkdir(parents=True, exist_ok=True)
                
                try:
                    shutil.copy2(original_path, target_dir / original_path.name)
                except Exception as e:
                    logging.error(f"Failed to copy profile {original_path} to {target_dir}: {e}")