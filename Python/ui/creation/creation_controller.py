import os
import logging
import shutil
import requests
from Python import constants

class CreationController:
    """
    Handles the business logic for creating game launchers and managing
    associated files (profiles, artwork, etc.).
    """
    def __init__(self, main_window):
        self.main_window = main_window
        self.config = main_window.config

    def validate_prerequisites(self, games):
        """
        Checks if necessary files (like the launcher executable) exist.
        Returns a list of missing items.
        """
        missing = []
        
        # Check Launcher Executable if configured
        launcher_exe = self.config.launcher_executable
        if launcher_exe and not os.path.exists(launcher_exe):
            missing.append(f"Launcher Executable: {launcher_exe}")
            
        # Check other tools if enabled in games
        # This is a simplified check; a full check would iterate games and check specific enabled tools
        
        return missing

    def create_all(self, games, progress_callback=None):
        """
        Process a list of games to create launchers and profiles.
        """
        processed = 0
        failed = 0
        
        for i, game in enumerate(games):
            if progress_callback:
                # Allow cancellation
                should_continue = progress_callback(i, len(games), game.get('name_override', game.get('name')))
                if not should_continue:
                    break
            
            try:
                self._create_single_game(game)
                processed += 1
            except Exception as e:
                logging.error(f"Failed to create {game.get('name')}: {e}")
                failed += 1
                
        return {'processed_count': processed, 'failed_count': failed}

    def _create_single_game(self, game_data):
        """Creates the launcher and profile for a single game."""
        from Python.ui.name_utils import make_safe_filename
        
        name = game_data.get('name_override') or game_data.get('name')
        safe_name = make_safe_filename(name)
        
        # 1. Create Profile Directory
        profile_dir = os.path.join(self.config.profiles_dir, safe_name)
        if not os.path.exists(profile_dir):
            os.makedirs(profile_dir)
            
        # 2. Create Launcher (Copy executable and rename)
        if self.config.launchers_dir and self.config.launcher_executable:
            if not os.path.exists(self.config.launchers_dir):
                os.makedirs(self.config.launchers_dir)
                
            dest_launcher = os.path.join(self.config.launchers_dir, f"{safe_name}.exe")
            
            # Check overwrite
            if not os.path.exists(dest_launcher) or self.config.overwrite_states.get('launcher_executable', True):
                if os.path.exists(self.config.launcher_executable):
                    shutil.copy2(self.config.launcher_executable, dest_launcher)

        # 3. Create Game.ini
        self._write_game_ini(game_data, profile_dir)
        
        # 4. Download Artwork if requested
        if self.config.download_artwork:
            self.download_artwork(game_data, profile_dir)

    def _write_game_ini(self, game_data, profile_dir):
        """Writes the Game.ini file."""
        import configparser
        ini_path = os.path.join(profile_dir, "Game.ini")
        
        config = configparser.ConfigParser()
        config.optionxform = str # Preserve case
        
        def clean_path(path):
            if not path: return ""
            if path.startswith("> ") or path.startswith("< "):
                return path[2:]
            return path

        config['Game'] = {
            'Name': game_data.get('name_override', '') or game_data.get('name', ''),
            'Executable': game_data.get('name', ''),
            'Directory': game_data.get('directory', ''),
            'IsoPath': game_data.get('iso_path', '')
        }
        
        config['Options'] = {
            'RunAsAdmin': str(game_data.get('run_as_admin', False)),
            'HideTaskbar': str(game_data.get('hide_taskbar', False)),
            'Borderless': str(game_data.get('options', '0')),
            'UseKillList': str(game_data.get('kill_list_enabled', False)),
            'TerminateBorderlessOnExit': str(game_data.get('terminate_borderless_on_exit', False)),
            'KillList': game_data.get('kill_list', ''),
            'BackupSaves': 'False',
            'MaxBackups': '5'
        }

        config['Paths'] = {
            'ControllerMapperApp': clean_path(game_data.get('controller_mapper_path', '')),
            'ControllerMapperOptions': game_data.get('controller_mapper_options', ''),
            'ControllerMapperArguments': game_data.get('controller_mapper_arguments', ''),
            
            'BorderlessWindowingApp': clean_path(game_data.get('borderless_windowing_path', '')),
            'BorderlessWindowingOptions': game_data.get('borderless_windowing_options', ''),
            'BorderlessWindowingArguments': game_data.get('borderless_windowing_arguments', ''),
            
            'MultiMonitorTool': clean_path(game_data.get('multi_monitor_app_path', '')),
            'MultiMonitorOptions': game_data.get('multi_monitor_app_options', ''),
            'MultiMonitorArguments': game_data.get('multi_monitor_app_arguments', ''),
            
            'Player1Profile': clean_path(game_data.get('player1_profile', '')),
            'Player2Profile': clean_path(game_data.get('player2_profile', '')),
            'MediaCenterProfile': clean_path(game_data.get('mediacenter_profile', '')),
            'MultiMonitorGamingConfig': clean_path(game_data.get('mm_game_profile', '')),
            'MultiMonitorDesktopConfig': clean_path(game_data.get('mm_desktop_profile', '')),
            
            'LauncherExecutable': clean_path(game_data.get('launcher_executable', ''))
        }
        
        pre_launch = {}
        for i in range(1, 4):
            pre_launch[f'App{i}'] = clean_path(game_data.get(f'pre{i}_path', ''))
            pre_launch[f'App{i}Options'] = game_data.get(f'pre{i}_options', '')
            pre_launch[f'App{i}Arguments'] = game_data.get(f'pre{i}_arguments', '')
            pre_launch[f'App{i}Wait'] = '1' if game_data.get(f'pre_{i}_run_wait', False) else '0'
        config['PreLaunch'] = pre_launch
        
        post_launch = {}
        for i in range(1, 4):
            post_launch[f'App{i}'] = clean_path(game_data.get(f'post{i}_path', ''))
            post_launch[f'App{i}Options'] = game_data.get(f'post{i}_options', '')
            post_launch[f'App{i}Arguments'] = game_data.get(f'post{i}_arguments', '')
            post_launch[f'App{i}Wait'] = '1' if game_data.get(f'post_{i}_run_wait', False) else '0'
            
        post_launch['JustAfterLaunchApp'] = clean_path(game_data.get('just_after_launch_path', ''))
        post_launch['JustAfterLaunchOptions'] = game_data.get('just_after_launch_options', '')
        post_launch['JustAfterLaunchArguments'] = game_data.get('just_after_launch_arguments', '')
        post_launch['JustAfterLaunchWait'] = '1' if game_data.get('just_after_launch_run_wait', False) else '0'
        
        post_launch['JustBeforeExitApp'] = clean_path(game_data.get('just_before_exit_path', ''))
        post_launch['JustBeforeExitOptions'] = game_data.get('just_before_exit_options', '')
        post_launch['JustBeforeExitArguments'] = game_data.get('just_before_exit_arguments', '')
        post_launch['JustBeforeExitWait'] = '1' if game_data.get('just_before_exit_run_wait', False) else '0'
        config['PostLaunch'] = post_launch
        
        config['Sequences'] = {
            'LaunchSequence': ",".join(self.config.launch_sequence),
            'ExitSequence': ",".join(self.config.exit_sequence)
        }

        with open(ini_path, 'w') as f:
            config.write(f)

    def download_artwork(self, game_data, profile_dir):
        """Downloads artwork for the game from Steam CDN."""
        steam_id = str(game_data.get('steam_id', ''))
        
        if not steam_id or steam_id == 'NOT_FOUND_IN_DATA':
            logging.warning(f"Skipping artwork download for {game_data.get('name')}: No Steam ID")
            return

        # Steam CDN URL patterns
        # Header: https://cdn.cloudflare.steamstatic.com/steam/apps/{app_id}/header.jpg
        # Library Hero: https://cdn.cloudflare.steamstatic.com/steam/apps/{app_id}/library_hero.jpg
        # Logo: https://cdn.cloudflare.steamstatic.com/steam/apps/{app_id}/logo.png
        
        assets = {
            "header.jpg": f"https://cdn.cloudflare.steamstatic.com/steam/apps/{steam_id}/header.jpg",
            "library_hero.jpg": f"https://cdn.cloudflare.steamstatic.com/steam/apps/{steam_id}/library_hero.jpg",
            "logo.png": f"https://cdn.cloudflare.steamstatic.com/steam/apps/{steam_id}/logo.png"
        }
        
        # Also try to get the icon
        # Icon URL requires a hash which we don't have easily without the API, 
        # but we can try to fetch the store page or use a third party service if needed.
        # For now, we'll stick to the reliable CDN assets.

        for filename, url in assets.items():
            try:
                save_path = os.path.join(profile_dir, filename)
                
                # Skip if exists
                if os.path.exists(save_path):
                    continue
                    
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    with open(save_path, 'wb') as f:
                        f.write(response.content)
                    logging.info(f"Downloaded {filename} for Steam ID {steam_id}")
                else:
                    logging.warning(f"Could not download {filename} for Steam ID {steam_id} (Status: {response.status_code})")
            except Exception as e:
                logging.error(f"Error downloading {filename} for Steam ID {steam_id}: {e}")
