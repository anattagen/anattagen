import os
import shutil
import configparser
import logging
from PyQt6.QtWidgets import QProgressDialog, QMessageBox, QCheckBox, QWidget
from PyQt6.QtCore import Qt, QCoreApplication
from Python import constants
from Python.models import AppConfig
from Python.ui.name_utils import make_safe_filename
from .file_propagator import FilePropagator
from .joystick_profile_manager import JoystickProfileManager

class CreationController:
    """Controller class for creating game environments"""
    def __init__(self, main_window):
        """Initialize the controller

        Args:
            main_window: The main application window instance.
        """
        self.main_window = main_window
        self.config = main_window.config
        self.parent_widget = main_window
        self.logger = logging.getLogger(__name__)

        # Get template paths from constants
        self.launcher_template_path = constants.LAUNCHER_TEMPLATE_PATH
        self.joystick_template_path = constants.JOYSTICK_TEMPLATE_PATH
        self.desktop_template_path = constants.DESKTOP_TEMPLATE_PATH
        self.triggers_template_path = constants.TRIGGERS_TEMPLATE_PATH
        self.kbm_template_path = constants.KBM_TEMPLATE_PATH
        # Initialize helpers
        self.propagator = FilePropagator(self.config.profiles_dir, self.config.launchers_dir)
        self.joystick_manager = JoystickProfileManager()
        
    def create_all(self, selected_games=None):
        """Create environments for selected games
        
        Args:
            selected_games: Optional list of selected games. If None, gets selections from the editor table.
            
        Returns:
            Dictionary with creation results
        """
        # Setup progress tracking
        processed_count = 0
        failed_count = 0
        creation_cancelled = False
                
        if not selected_games:
            QMessageBox.warning(self.parent_widget, "No Games Selected", "No games were selected for creation.")
            return {"processed_count": 0, "failed_count": 0, "cancelled": False}
        
        # Create progress dialog
        progress = QProgressDialog("Creating game environments...", "Cancel", 0, len(selected_games), self.parent_widget)
        progress.setWindowTitle("Creating Game Environments")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()
        
        # Process each selected game
        for i, game_data in enumerate(selected_games):
            # Update progress
            progress.setValue(i)
            progress.setLabelText(f"Creating environment for: {game_data.get('name_override', 'Unknown Game')}")
            QCoreApplication.processEvents()
            
            # Check if operation was cancelled
            if progress.wasCanceled():
                creation_cancelled = True
                break
                
            try:
                # Process the game
                self._create_single_game_environment(game_data)
                processed_count += 1
                
            except Exception as e:
                self.logger.error(f"Failed to create environment for {game_data.get('name_override', 'Unknown')}: {str(e)}")
                failed_count += 1
                
            # Process events to keep UI responsive
            QCoreApplication.processEvents()
        
        # Close progress dialog
        progress.setValue(len(selected_games))
        progress.close()
        
        # Update status bar with results
        status_message = f"Processed {processed_count} games"
        if failed_count > 0:
            status_message += f", {failed_count} failed"
        if creation_cancelled:
            status_message += " (cancelled)"
            
        return {
            "processed_count": processed_count,
            "failed_count": failed_count,
            "cancelled": creation_cancelled
        }
            
    def _create_single_game_environment(self, game_data):
        """Create environment for a single game
        
        Args:
            game_data: Dictionary containing game data
            
        Returns:
            True on success, False on failure
        """
        try:
            # Get name for the game environment
            game_name = game_data.get('name_override', '')
            if not game_name:
                game_name = os.path.splitext(game_data.get('executable', 'Unknown'))[0]
                
            # Ensure we have valid profiles and launchers directories
            if not self.propagator.ensure_directories_exist():
                return False

            # Create profile folder if option is enabled
            profile_folder = None
            if self.config.create_profile_folders:
                profile_folder = self.propagator.create_profile_directory(game_name)
                if profile_folder:
                    self._create_game_ini(profile_folder, game_data)

            # Create launcher if option is enabled
            if self.config.create_overwrite_launcher:
                launcher_path = self.propagator.create_launcher(
                    game_name=game_name,
                    executable_path=game_data.get('executable', ''),
                    working_dir=game_data.get('directory', ''),
                    arguments=game_data.get('arguments', ''),
                    profile_dir=profile_folder
                )
                if launcher_path:
                    self.propagator.create_shortcut(game_name, launcher_path)

            # Create joystick profiles if option is enabled
            if self.config.create_overwrite_joystick_profiles and profile_folder:
                self.joystick_manager.create_profiles(game_name, profile_folder)
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating game environment for {game_name}: {str(e)}")
            return False
            
    def _validate_directories(self):
        """Validate and create required directories if they don't exist
        
        Returns:
            True if directories are valid, False otherwise
        """
        # Check profiles directory
        if not self.config.profiles_dir:
            QMessageBox.warning(self.parent_widget, "Configuration Error", "Profiles directory not set in Setup tab.")
            return False
            
        # Check launchers directory
        if not self.config.launchers_dir:
            QMessageBox.warning(self.parent_widget, "Configuration Error", "Launchers directory not set in Setup tab.")
            return False
            
        # Create directories if they don't exist
        try:
            os.makedirs(self.config.profiles_dir, exist_ok=True)
            os.makedirs(self.config.launchers_dir, exist_ok=True)
            return True
        except Exception as e:
            self.logger.error(f"Error creating directories: {str(e)}")
            return False
        
    def _create_profile_folder(self, game_name, game_data):
        """Create profile folder for the game
        
        Args:
            game_name: Name of the game
            game_data: Dictionary containing game data
        """
        # Create safe folder name
        safe_name = make_safe_filename(game_name)
        
        # Create the profile folder path
        profile_folder = os.path.join(self.config.profiles_dir, safe_name)
        
        # Create the folder if it doesn't exist
        os.makedirs(profile_folder, exist_ok=True)
        
        # Create Game.ini in the profile folder
        self._create_game_ini(profile_folder, game_data)
        
    def _create_game_ini(self, profile_folder, game_data):
        """Create Game.ini file in the profile folder
        
        Args:
            profile_folder: Path to the profile folder
            game_data: Dictionary containing game data
        """
        # Create config parser
        config = configparser.ConfigParser()
        config.optionxform = str  # Preserve case for keys
        
        # Create sections
        config["Game"] = {}
        config["Paths"] = {}
        config["Options"] = {}
        config["Sequences"] = {}
        
        # Fill Game section
        config["Game"]["Name"] = game_data.get('name_override', '')
        config["Game"]["Executable"] = game_data.get('executable', '')
        config["Game"]["Directory"] = game_data.get('directory', '')
        config["Game"]["Arguments"] = game_data.get('arguments', '')
        if game_data.get('steam_id', ''):
            config["Game"]["SteamID"] = game_data.get('steam_id', '')
            
        # Fill Options section
        config["Options"]["RunAsAdmin"] = str(game_data.get('as_admin', False))
        config["Options"]["HideTaskbar"] = str(game_data.get('no_tb', False))
        
        # Set borderless option based on the value (E, K, or empty)
        borderless = game_data.get('borderless', '')
        is_borderless = borderless in ('E', 'K')
        config["Options"]["BorderlessWindow"] = str(is_borderless)
        config["Options"]["TerminateBorderlessOnExit"] = str(borderless == 'K')

        # Fill Paths section with path settings
        path_fields = {
            "p1_profile": "Player1ProfileFile",
            "p2_profile": "Player2ProfileFile",
            "desktop_ctrl": "DesktopControllerFile",
            "game_monitor_cfg": "GameMonitorConfigFile",
            "desktop_monitor_cfg": "DesktopMonitorConfigFile",
            "post1": "PostLaunch1",
            "post2": "PostLaunch2",
            "post3": "PostLaunch3",
            "pre1": "PreLaunch1",
            "pre2": "PreLaunch2",
            "pre3": "PreLaunch3",
            "just_after": "JustAfterLaunch",
            "just_before": "JustBeforeExit"
        }
        
        for field, ini_key in path_fields.items():
            value = game_data.get(field, '')
            # Parse the CEN/LC indicator if present
            mode = "CEN"  # Default
            if value.startswith('>'):
                mode = "LC"
                value = value[1:]
            elif value.startswith('<'):
                mode = "CEN"
                value = value[1:]
                
            # Store path and mode
            if value:
                config["Paths"][ini_key] = value
                config["Paths"][f"{ini_key}Mode"] = mode

        # Get launch and exit sequences from the config model
        config["Sequences"]["LaunchSequence"] = ",".join(self.config.launch_sequence)
        config["Sequences"]["ExitSequence"] = ",".join(self.config.exit_sequence)
            
        # Write the config to Game.ini
        ini_path = os.path.join(profile_folder, "Game.ini")
        with open(ini_path, 'w', encoding='utf-8') as f:
            config.write(f)
        
    def _create_launcher(self, game_name, game_data):
        """Create launcher batch file for the game
        
        Args:
            game_name: Name of the game
            game_data: Dictionary containing game data
        """
        # Create safe file name
        safe_name = make_safe_filename(game_name)
        
        # Get the launcher template
        template = self._read_template_file(self.launcher_template_path)
        if not template:
            self.logger.error(f"Failed to read launcher template from {self.launcher_template_path}")
            return
            
        # Create path to the profile folder
        profile_folder = os.path.join(self.config.profiles_dir, safe_name)
        
        # Replace placeholders in the template
        launcher_content = template.replace("{{GAME_NAME}}", game_name)
        launcher_content = launcher_content.replace("{{PROFILE_FOLDER}}", profile_folder)
        launcher_content = launcher_content.replace("{{EXECUTABLE}}", game_data.get('executable', ''))
        launcher_content = launcher_content.replace("{{DIRECTORY}}", game_data.get('directory', ''))
        launcher_content = launcher_content.replace("{{ARGUMENTS}}", game_data.get('arguments', ''))
        
        # Create the launcher file path
        launcher_path = os.path.join(self.config.launchers_dir, f"{safe_name}.bat")
        
        # Write the launcher file
        with open(launcher_path, 'w', encoding='utf-8') as f:
            f.write(launcher_content)
            
        # Create a shortcut if possible (using Shortcut.exe in bin folder)
        self._create_shortcut(game_name, launcher_path, game_data)
        
    def _read_template_file(self, template_path):
        """Read a template file
        
        Args:
            template_path: Path to the template file
            
        Returns:
            Contents of the template file or empty string on error
        """
        try:
            if os.path.exists(template_path):
                with open(template_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                self.logger.error(f"Template file not found: {template_path}")
                return ""
        except Exception as e:
            self.logger.error(f"Error reading template file: {str(e)}")
            return ""
            
    def _create_shortcut(self, game_name, target_path, game_data):
        """Create a shortcut to the launcher
        
        Args:
            game_name: Name of the game
            target_path: Path to the target file
            game_data: Dictionary containing game data
        """
        try:
            # Get the path to Shortcut.exe
            shortcut_exe = constants.SHORTCUT_EXE_PATH
            
            # Check if Shortcut.exe exists
            if not os.path.exists(shortcut_exe):
                self.logger.error(f"Shortcut.exe not found at {shortcut_exe}")
                return
                
            # Create safe filename for the shortcut
            safe_name = make_safe_filename(game_name)
            
            # Create the shortcut file path
            shortcut_path = os.path.join(self.config.launchers_dir, f"{safe_name}.lnk")
            
            # Build the command to create the shortcut
            import subprocess
            cmd = [
                shortcut_exe,
                "/F:" + shortcut_path,
                "/A:C",
                "/T:" + target_path,
                "/W:" + os.path.dirname(target_path),
                "/N:" + game_name
            ]
            
            # Add icon if Joystick.ico is available
            if os.path.exists(constants.JOYSTICK_ICON_PATH):
                cmd.append("/I:" + constants.JOYSTICK_ICON_PATH)
                
            # Execute the command
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.logger.error(f"Error creating shortcut: {result.stderr}")
                
        except Exception as e:
            self.logger.error(f"Error creating shortcut: {str(e)}")
            
    def _create_joystick_profiles(self, game_name, game_data):
        """Create joystick profiles for the game
        
        Args:
            game_name: Name of the game
            game_data: Dictionary containing game data
        """
        # Create safe folder name
        safe_name = make_safe_filename(game_name)
        
        # Create the profile folder path
        profile_folder = os.path.join(self.config.profiles_dir, safe_name)
        
        # Create the profiles folder if it doesn't exist
        os.makedirs(os.path.join(profile_folder, "Profiles"), exist_ok=True)
        
        # Create the game joystick profile
        self._create_joystick_profile(game_name, profile_folder, "Game", self.joystick_template_path)
        
        # Create the desktop joystick profile
        self._create_joystick_profile(game_name, profile_folder, "Desktop", self.desktop_template_path)
        
        # Create the triggers profile
        self._create_joystick_profile(game_name, profile_folder, "Trigger", self.triggers_template_path)
        
        # Create the KBM profile
        self._create_joystick_profile(game_name, profile_folder, "KBM", self.kbm_template_path)
        
    def _create_joystick_profile(self, game_name, profile_folder, profile_type, template_path):
        """Create a specific joystick profile
        
        Args:
            game_name: Name of the game
            profile_folder: Path to the profile folder
            profile_type: Type of profile (Game, Desktop, Trigger, KBM)
            template_path: Path to the template file
        """
        try:
            # Read the template
            template = self._read_template_file(template_path)
            if not template:
                return
                
            # Create safe filename
            safe_name = make_safe_filename(game_name)
            
            # Replace placeholders
            profile_content = template.replace("{{GAME_NAME}}", game_name)
            
            # Create profile filename
            if profile_type == "Game":
                filename = f"{safe_name}.gamecontroller.amgp"
            elif profile_type == "Desktop":
                filename = f"{safe_name}_Desktop.gamecontroller.amgp"
            elif profile_type == "Trigger":
                filename = f"{safe_name}_Trigger.gamecontroller.amgp"
            else:  # KBM
                filename = f"{safe_name}_KBM.gamecontroller.amgp"
                
            # Create the profile file path
            profile_path = os.path.join(profile_folder, "Profiles", filename)
            
            # Write the profile file
            with open(profile_path, 'w', encoding='utf-8') as f:
                f.write(profile_content)
                
        except Exception as e:
            self.logger.error(f"Error creating {profile_type} joystick profile: {str(e)}")
        launcher_path = self.propagator.create_launcher(
            game_name=game_name,
            executable_path=game_data.get('executable', ''),
            working_dir=game_data.get('directory', ''),
            arguments=game_data.get('arguments', ''),
            profile_dir=profile_folder
        )
        if launcher_path:
            self.propagator.create_shortcut(game_name, launcher_path)