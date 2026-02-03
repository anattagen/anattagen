#!/usr/bin/env python3
"""
Launcher.py - Game Launcher Script

A Python port of the Launcher.ahk script for launching games with pre/post actions
"""

import os
import sys
import subprocess
import configparser
import time
import ctypes
import shutil
import datetime
import tempfile
import signal
import psutil
import logging
from pathlib import Path
import shlex
from typing import Dict, List, Optional, Tuple, Union
import platform
import argparse
import glob

# Conditional imports for Windows
if sys.platform == 'win32':
    import winreg
    import win32gui
    import win32con
    import win32process
    import win32api

# Import the new sequence executor
try:
    from Python.sequence_executor import SequenceExecutor
except ImportError:
    from sequence_executor import SequenceExecutor

class DynamicSplash:
    """Handles a dynamic splash screen using Pygame and Win32GUI for transparency."""
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.image_path = None
        self.mode = None  # 'fullscreen' or 'notification'
        self.hwnd = None
        self.running = False
        self._find_image()

    def _find_image(self):
        if not self.base_dir or not os.path.exists(self.base_dir):
            return

        extensions = ['jpg', 'jpeg', 'png', 'gif']
        fs_names = ['Backdrop', 'background', 'fanart', 'wallpaper']
        notif_names = ['box-art', 'boxart', 'coverart', 'cover-art']

        # Helper to search case-insensitive
        def search(names):
            for name in names:
                for ext in extensions:
                    pattern = os.path.join(self.base_dir, f"{name}.{ext}")
                    matches = glob.glob(pattern) # glob is case-insensitive on Windows usually
                    if not matches:
                        # Try explicit case variations if glob didn't catch it
                        matches = glob.glob(os.path.join(self.base_dir, f"{name.lower()}.{ext}"))
                    if matches:
                        return matches[0]
            return None

        # Check Fullscreen first
        self.image_path = search(fs_names)
        if self.image_path:
            self.mode = 'fullscreen'
            return

        # Check Notification area
        self.image_path = search(notif_names)
        if self.image_path:
            self.mode = 'notification'

    def show(self):
        if not self.image_path:
            return

        try:
            import pygame
            pygame.init()
            
            # Load image
            img = pygame.image.load(self.image_path)
            info = pygame.display.Info()
            screen_w, screen_h = info.current_w, info.current_h

            if self.mode == 'fullscreen':
                # Scale to fill screen
                img = pygame.transform.scale(img, (screen_w, screen_h))
                self.screen = pygame.display.set_mode((screen_w, screen_h), pygame.NOFRAME)
            else:
                # Notification mode: Scale to 0.6 screen height, maintain aspect
                target_h = int(screen_h * 0.6)
                rect = img.get_rect()
                aspect = rect.width / rect.height
                target_w = int(target_h * aspect)
                img = pygame.transform.smoothscale(img, (target_w, target_h))
                
                # Position bottom right
                x = screen_w - target_w - 20
                y = screen_h - target_h - 40
                os.environ['SDL_VIDEO_WINDOW_POS'] = f"{x},{y}"
                self.screen = pygame.display.set_mode((target_w, target_h), pygame.NOFRAME)

            # Get HWND for transparency
            self.hwnd = pygame.display.get_wm_info()["window"]
            
            # Set layered window attributes for alpha blending the whole window
            if platform.system() == 'Windows':
                ex_style = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)
                win32gui.SetWindowLong(self.hwnd, win32con.GWL_EXSTYLE, ex_style | win32con.WS_EX_LAYERED)
                # Start fully transparent
                win32gui.SetLayeredWindowAttributes(self.hwnd, 0, 0, win32con.LWA_ALPHA)
            
            self.screen.blit(img, (0, 0))
            pygame.display.flip()
            self.running = True
            
            # Fade In
            self._fade(0, 255)
            
        except Exception as e:
            logging.error(f"Failed to show dynamic splash: {e}")
            self.running = False

    def close(self):
        if self.running:
            # Fade Out
            self._fade(255, 0)
            try:
                import pygame
                pygame.quit()
            except:
                pass
            self.running = False

    def _fade(self, start, end):
        if platform.system() == 'Windows' and self.hwnd:
            step = 5 if start < end else -5
            for alpha in range(start, end + step, step):
                # Clamp alpha
                alpha = max(0, min(255, alpha))
                win32gui.SetLayeredWindowAttributes(self.hwnd, 0, alpha, win32con.LWA_ALPHA)
                # Pump events to keep window responsive
                try:
                    import pygame
                    pygame.event.pump()
                    pygame.time.delay(5)
                except:
                    break

class GameLauncher:
    def __init__(self):
        # Initialize variables
        if getattr(sys, 'frozen', False):
            self.home = os.path.dirname(sys.executable)
            # Attach to parent console to allow --help to print to stdout
            if platform.system() == 'Windows':
                try:
                    if ctypes.windll.kernel32.AttachConsole(-1):
                        sys.stdout = open("CONOUT$", "w")
                        sys.stderr = open("CONOUT$", "w")
                except Exception:
                    pass
        else:
            # If running from source (Python dir), set home to project root
            current_dir = os.path.dirname(os.path.abspath(__file__))
            if os.path.basename(current_dir).lower() == 'python':
                self.home = os.path.dirname(current_dir)
            else:
                self.home = current_dir
            
        # Ensure stdout/stderr exist to prevent argparse crashes (e.g. pythonw or noconsole)
        if sys.stdout is None:
            sys.stdout = open(os.devnull, 'w')
        if sys.stderr is None:
            sys.stderr = open(os.devnull, 'w')
            
        self.source = os.path.join(self.home, "Python")
        self.binhome = os.path.join(self.home, "bin")
        self.curpidf = os.path.join(self.home, "rjpids.ini")
        self.current_pid = os.getpid()
        self.multi_instance = 0
        self.game_path = ""
        self.game_name = ""
        self.game_dir = ""
        self.plink = ""
        self.scpath = ""
        self.scextn = ""
        self.ini_path = ""
        self.exe_list = ""
        self.joymessage = "No joysticks detected"
        self.joycount = 0
        self.mapper_extension = "gamecontroller.amgp"  # Default for antimicrox
        
        self.game_process = None
        self.borderless_process = None
        self.dynamic_splash = None
        self.args = None
        self.iso_path = ""

        # Set up message display (logging) early
        self.setup_message_display()

        self.update_splash_progress(10, "Initializing...")

        # Get command line arguments
        self.update_splash_progress(20, "Parsing arguments...")
        self.parse_arguments()
        
        # Check if we're running as admin
        self.update_splash_progress(30, "Checking permissions...")
        self.is_admin = self.check_admin()
        
        # Check for other instances
        self.update_splash_progress(40, "Checking instances...")
        if not self.check_instances():
            sys.exit(0)
        
        # Load configuration
        self.update_splash_progress(50, "Loading configuration...")
        self.load_config()
        
        # Modify config if requested via CLI
        if self.args and (self.args.set or self.args.clear):
            self.modify_config()
            self.load_config() # Reload to apply changes

        # Initialize joystick detection
        self.update_splash_progress(70, "Detecting input devices...")
        self.detect_joysticks()
        
        # Initialize the sequence executor
        self.update_splash_progress(90, "Preparing execution sequences...")
        self.executor = SequenceExecutor(self)
        
        # Close splash screen after initialization is done
        self.update_splash_progress(100, "Ready to launch!")
        self.close_splash()
        
        # Start dynamic splash (after static splash closes)
        self.dynamic_splash = DynamicSplash(self.scpath if self.scpath else self.home)
        self.dynamic_splash.show()

    def parse_arguments(self):
        """Parse command line arguments"""
        parser = argparse.ArgumentParser(description="Game Launcher - A portable environment manager for games.")
        parser.add_argument("target", nargs="?", help="Target shortcut or executable")
        parser.add_argument("--home", help="Override home directory for asset redirection")
        parser.add_argument("--set", action="append", help="Set config value: Section.Key=Value")
        parser.add_argument("--clear", action="append", help="Clear config value: Section.Key")
        
        # Use parse_known_args to allow for other potential flags
        self.args, unknown = parser.parse_known_args()
        args = self.args
        if args.home:
            self.home = os.path.abspath(args.home)
            self.source = os.path.join(self.home, "Python")
            self.binhome = os.path.join(self.home, "bin")
            self.curpidf = os.path.join(self.home, "rjpids.ini")
            
        if args.target:
            self.plink = args.target
            # Get file extension
            _, self.scpath, self.scextn, self.game_name = self.split_path(self.plink)
            # Display message
            self.show_message(f"Launching: {self.plink}")
        else:
            self.show_message("No Item Detected")
            self.close_splash()
            time.sleep(3)
            sys.exit(0)
    
    def check_admin(self):
        """Check if running as administrator"""
        try:
            if platform.system() == 'Windows':
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                return os.geteuid() == 0
        except:
            return False
    
    def setup_message_display(self):
        """Set up message display (tooltip or console)"""
        # Configure logging to file
        log_file = os.path.join(self.home, "launcher.log")
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filemode='w'
        )

        # Redirect stderr to capture crashes
        def handle_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
        
        sys.excepthook = handle_exception
        logging.info(f"Launcher started. Home directory: {self.home}")
    
    def show_message(self, message):
        """Show a message to the user"""
        print(message)
        logging.info(message)
        try:
            import pyi_splash
            if pyi_splash.is_alive():
                pyi_splash.update_text(message)
        except ImportError:
            pass
        # In a full implementation, this could update a GUI or show a notification

    def update_splash_progress(self, percent, message):
        """Update splash screen with text-based progress bar"""
        try:
            import pyi_splash
            if pyi_splash.is_alive():
                bar_len = 25
                filled = int(bar_len * percent / 100)
                bar = "█" * filled + "-" * (bar_len - filled)
                pyi_splash.update_text(f"{message}\n[{bar}] {percent}%")
        except ImportError:
            pass
        logging.info(f"Progress {percent}%: {message}")
    
    def check_instances(self):
        """Check for other instances of the launcher"""
        if os.path.exists(self.curpidf):
            config = configparser.ConfigParser()
            config.read(self.curpidf)
            
            try:
                instance_pid = int(config.get('Instance', 'pid', fallback='0'))
                self.multi_instance = int(config.get('Instance', 'multi_instance', fallback='0'))
                
                if self.multi_instance == 1:
                    return True
                
                # Check if the process is still running
                if instance_pid != 0 and instance_pid != self.current_pid:
                    try:
                        process = psutil.Process(instance_pid)
                        if process.is_running():
                            # Ask user if they want to terminate the running instance

                            response = input("Would you like to terminate the running instance? (y/n): ")
                            if response.lower() == 'y':
                                process.terminate()
                                time.sleep(1)
                                if process.is_running():
                                    process.kill()
                            else:
                                return False
                    except psutil.NoSuchProcess:
                        pass  # Process doesn't exist, continue
            except Exception as e:
                pass
        
        return True
    
    def load_config(self):
        """Load configuration from Game.ini"""
        # First check if there's a Game.ini in the same directory as the shortcut
        game_ini = os.path.join(self.scpath, "Game.ini")
        
        if not os.path.exists(game_ini):
            # Fall back to config.ini in the home directory
            game_ini = os.path.join(self.home, "config.ini")
        
        if not os.path.exists(game_ini):
            self.show_message("No configuration file found")
            return
        self.ini_path = game_ini
        
        config = configparser.ConfigParser()
        config.read(game_ini)
        
        # Load game information
        if 'Game' in config:
            self.game_path = config.get('Game', 'Executable', fallback='')
            self.game_dir = config.get('Game', 'Directory', fallback='')
            self.game_name = config.get('Game', 'Name', fallback=self.game_name)
            self.iso_path = config.get('Game', 'IsoPath', fallback='')
        
        # Load paths
        if 'Paths' in config:
            self.controller_mapper_app = config.get('Paths', 'ControllerMapperApp', fallback='')
            self.controller_mapper_options = config.get('Paths', 'ControllerMapperOptions', fallback='')
            self.controller_mapper_arguments = config.get('Paths', 'ControllerMapperArguments', fallback='')
            self.borderless_app = config.get('Paths', 'BorderlessWindowingApp', fallback='')
            self.borderless_options = config.get('Paths', 'BorderlessWindowingOptions', fallback='')
            self.borderless_arguments = config.get('Paths', 'BorderlessWindowingArguments', fallback='')
            self.multimonitor_tool = config.get('Paths', 'MultiMonitorTool', fallback='')
            self.multimonitor_options = config.get('Paths', 'MultiMonitorOptions', fallback='')
            self.multimonitor_arguments = config.get('Paths', 'MultiMonitorArguments', fallback='')
            self.player1_profile = config.get('Paths', 'Player1Profile', fallback='')
            self.player2_profile = config.get('Paths', 'Player2Profile', fallback='')
            self.mediacenter_profile = config.get('Paths', 'MediaCenterProfile', fallback='')
            self.mm_game_config = config.get('Paths', 'MultiMonitorGamingConfig', fallback='')
            self.mm_desktop_config = config.get('Paths', 'MultiMonitorDesktopConfig', fallback='')
            self.cloud_app = config.get('Paths', 'CloudApp', fallback='')
            self.cloud_app_options = config.get('Paths', 'CloudAppOptions', fallback='')
            self.cloud_app_arguments = config.get('Paths', 'CloudAppArguments', fallback='')
        
        # Load options
        if 'Options' in config:
            self.run_as_admin = config.getboolean('Options', 'RunAsAdmin', fallback=False)
            self.hide_taskbar = config.getboolean('Options', 'HideTaskbar', fallback=False)
            self.borderless = config.get('Options', 'Borderless', fallback='0')
            self.use_kill_list = config.getboolean('Options', 'UseKillList', fallback=False)
            self.terminate_borderless_on_exit = config.getboolean('Options', 'TerminateBorderlessOnExit', fallback=False)
            self.kill_list_str = config.get('Options', 'KillList', fallback='')
            self.kill_list = [x.strip() for x in self.kill_list_str.split(',') if x.strip()]
            self.backup_saves = config.getboolean('Options', 'BackupSaves', fallback=False)
            self.max_backups = config.getint('Options', 'MaxBackups', fallback=5)

        # Load pre-launch apps
        if 'PreLaunch' in config:
            self.pre_launch_app_1 = config.get('PreLaunch', 'App1', fallback='')
            self.pre_launch_app_1_options = config.get('PreLaunch', 'App1Options', fallback='')
            self.pre_launch_app_1_arguments = config.get('PreLaunch', 'App1Arguments', fallback='')
            self.pre_launch_app_2 = config.get('PreLaunch', 'App2', fallback='')
            self.pre_launch_app_2_options = config.get('PreLaunch', 'App2Options', fallback='')
            self.pre_launch_app_2_arguments = config.get('PreLaunch', 'App2Arguments', fallback='')
            self.pre_launch_app_3 = config.get('PreLaunch', 'App3', fallback='')
            self.pre_launch_app_3_options = config.get('PreLaunch', 'App3Options', fallback='')
            self.pre_launch_app_3_arguments = config.get('PreLaunch', 'App3Arguments', fallback='')
            self.pre_launch_app_1_wait = config.get('PreLaunch', 'App1Wait', fallback='0') == '1'
            self.pre_launch_app_2_wait = config.get('PreLaunch', 'App2Wait', fallback='0') == '1'
            self.pre_launch_app_3_wait = config.get('PreLaunch', 'App3Wait', fallback='0') == '1'
        
        # Load post-launch apps
        if 'PostLaunch' in config:
            self.post_launch_app_1 = config.get('PostLaunch', 'App1', fallback='')
            self.post_launch_app_1_options = config.get('PostLaunch', 'App1Options', fallback='')
            self.post_launch_app_1_arguments = config.get('PostLaunch', 'App1Arguments', fallback='')
            self.post_launch_app_2 = config.get('PostLaunch', 'App2', fallback='')
            self.post_launch_app_2_options = config.get('PostLaunch', 'App2Options', fallback='')
            self.post_launch_app_2_arguments = config.get('PostLaunch', 'App2Arguments', fallback='')
            self.post_launch_app_3 = config.get('PostLaunch', 'App3', fallback='')
            self.post_launch_app_3_options = config.get('PostLaunch', 'App3Options', fallback='')
            self.post_launch_app_3_arguments = config.get('PostLaunch', 'App3Arguments', fallback='')
            self.post_launch_app_1_wait = config.get('PostLaunch', 'App1Wait', fallback='0') == '1'
            self.post_launch_app_2_wait = config.get('PostLaunch', 'App2Wait', fallback='0') == '1'
            self.post_launch_app_3_wait = config.get('PostLaunch', 'App3Wait', fallback='0') == '1'
            self.just_after_launch_app = config.get('PostLaunch', 'JustAfterLaunchApp', fallback='')
            self.just_after_launch_options = config.get('PostLaunch', 'JustAfterLaunchOptions', fallback='')
            self.just_after_launch_arguments = config.get('PostLaunch', 'JustAfterLaunchArguments', fallback='')
            self.just_before_exit_app = config.get('PostLaunch', 'JustBeforeExitApp', fallback='')
            self.just_before_exit_options = config.get('PostLaunch', 'JustBeforeExitOptions', fallback='')
            self.just_before_exit_arguments = config.get('PostLaunch', 'JustBeforeExitArguments', fallback='')
            self.just_after_launch_wait = config.get('PostLaunch', 'JustAfterLaunchWait', fallback='0') == '1'
            self.just_before_exit_wait = config.get('PostLaunch', 'JustBeforeExitWait', fallback='0') == '1'
        
        # Load sequences
        if 'Sequences' in config:
            # Get launch sequence
            launch_sequence_str = config.get('Sequences', 'LaunchSequence', fallback='')
            if launch_sequence_str:
                self.launch_sequence = launch_sequence_str.split(',')
            else:
                # Default launch sequence
                self.launch_sequence = [
                    "Controller-Mapper", 
                    "Monitor-Config", 
                    "No-TB",
                    "Pre1", 
                    "Pre2", 
                    "Pre3", 
                    "Borderless"
                ]
            
            # Get exit sequence
            exit_sequence_str = config.get('Sequences', 'ExitSequence', fallback='')
            if exit_sequence_str:
                self.exit_sequence = exit_sequence_str.split(',')
            else:
                # Default exit sequence
                self.exit_sequence = [
                    "Post1", 
                    "Post2", 
                    "Post3", 
                    "Monitor-Config", 
                    "Taskbar",
                    "Controller-Mapper"
                ]

    def modify_config(self):
        """Modify the configuration file based on CLI arguments."""
        if not self.ini_path or not os.path.exists(self.ini_path):
            self.show_message("Config file not found, cannot modify.")
            return

        config = configparser.ConfigParser()
        config.optionxform = str # Preserve case
        config.read(self.ini_path)
        
        changed = False
        
        if self.args.set:
            for item in self.args.set:
                if '=' in item:
                    key_part, value = item.split('=', 1)
                    if '.' in key_part:
                        section, key = key_part.split('.', 1)
                        if not config.has_section(section):
                            config.add_section(section)
                        config.set(section, key, value)
                        changed = True
                        self.show_message(f"Set {section}.{key} = {value}")

        if self.args.clear:
            for item in self.args.clear:
                if '.' in item:
                    section, key = item.split('.', 1)
                    if config.has_section(section) and config.has_option(section, key):
                        config.remove_option(section, key)
                        changed = True
                        self.show_message(f"Cleared {section}.{key}")

        if changed:
            with open(self.ini_path, 'w') as f:
                config.write(f)
            self.show_message("Configuration updated.")

    def resolve_path(self, path):
        """Substitute variables in path."""
        if not path or not isinstance(path, str):
            return path
            
        # Define variables
        vars_map = {
            '$MAPPER': self.controller_mapper_app,
            '$BORDERLESS': self.borderless_app,
            '$MMONAPP': self.multimonitor_tool,
            '$CLOUDAPP': getattr(self, 'cloud_app', ''),
            '$GAMEDIR': self.game_dir,
            '$GAMEEXE': self.game_path,
            '$GAMENAME': self.game_name,
            '$HOME': self.home
        }
        
        # Simple replacement
        for var, value in vars_map.items():
            if var in path:
                path = path.replace(var, value)
        return path
    
    def detect_joysticks(self):
        """Detect connected joysticks"""
        try:
            import pygame
            pygame.init()
            pygame.joystick.init()
            
            self.joycount = pygame.joystick.get_count()
            if self.joycount > 0:
                self.joymessage = f"{self.joycount} joysticks detected"
                
                # Initialize each joystick
                for i in range(self.joycount):
                    joystick = pygame.joystick.Joystick(i)
                    joystick.init()

            else:
                self.joymessage = "No joysticks detected"
            
            pygame.quit()
        except ImportError:
            self.joymessage = "Pygame not installed, joystick detection disabled"
        except Exception as e:
            self.joymessage = f"Error detecting joysticks: {e}"
    
    def backup_save_files(self):
        """Backs up the saves directory if configured."""
        if not getattr(self, 'backup_saves', False):
            return

        # Determine save directory (default to Saves in profile dir)
        save_dir = os.path.join(self.home, "Saves")
        
        if not os.path.exists(save_dir):
            self.show_message("Save directory not found, skipping backup.")
            return

        backup_root = os.path.join(self.home, "Backups")
        if not os.path.exists(backup_root):
            os.makedirs(backup_root)

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_name = f"SaveBackup_{timestamp}"
        backup_path = os.path.join(backup_root, backup_name)

        try:
            shutil.make_archive(backup_path, 'zip', save_dir)
            self.show_message(f"Backed up saves to {backup_name}.zip")
            
            # Rotate backups
            backups = sorted([f for f in os.listdir(backup_root) if f.startswith("SaveBackup_") and f.endswith(".zip")])
            while len(backups) > self.max_backups:
                oldest = backups.pop(0)
                os.remove(os.path.join(backup_root, oldest))
                self.show_message(f"Removed old backup: {oldest}")
        except Exception as e:
            self.show_message(f"Backup failed: {e}")

    def mount_iso(self):
        """Mounts the configured ISO file."""
        iso_resolved = self.resolve_path(self.iso_path)
        if iso_resolved and os.path.exists(iso_resolved):
            self.show_message(f"Mounting ISO: {iso_resolved}")
            if platform.system() == 'Windows':
                cmd = f'powershell -Command "Mount-DiskImage -ImagePath \'{iso_resolved}\'"'
                self.run_process(cmd, wait=True)
            elif platform.system() == 'Darwin':
                self.run_process(f'hdiutil mount "{iso_resolved}"', wait=True)
            elif platform.system() == 'Linux':
                self.run_process(f'udisksctl loop-setup -f "{iso_resolved}"', wait=True)
                
            time.sleep(2) # Allow time for the drive to mount

    def unmount_iso(self):
        """Unmounts the configured ISO file."""
        iso_resolved = self.resolve_path(self.iso_path)
        if iso_resolved:
            self.show_message(f"Unmounting ISO: {iso_resolved}")
            if platform.system() == 'Windows':
                cmd = f'powershell -Command "Dismount-DiskImage -ImagePath \'{iso_resolved}\'"'
                self.run_process(cmd, wait=True)
            elif platform.system() == 'Darwin':
                # Attempt to detach; note that hdiutil usually requires the device node or mount point
                pass 
            elif platform.system() == 'Linux':
                pass

    def run_game(self):
        """Run the main game executable"""
        self.show_message(f"Launching game: {self.game_name}")
        
        # Prepare the command
        if not self.game_path:
            self.game_path = self.plink
        
        # Get the game directory
        if not self.game_dir:
            self.game_dir = os.path.dirname(self.game_path)
        
        # Close dynamic splash before launching the game
        if self.dynamic_splash:
            self.dynamic_splash.close()

        game_path_resolved = self.resolve_path(self.game_path)
        # Run the game
        if self.run_as_admin and platform.system() == 'Windows' and not self.is_admin:
            # Use PowerShell to run as admin
            cmd = f'powershell -Command "Start-Process \'{game_path_resolved}\' -Verb RunAs"'
            self.game_process = self.run_process(cmd, cwd=self.game_dir)
        else:
            self.game_process = self.run_process(f'"{game_path_resolved}"', cwd=self.game_dir)
        
        # Wait for the game to exit
        if self.game_process:
            self.game_process.wait()

    def run(self):
        """Main execution flow"""
        try:
            # Write current PID to the PID file
            self.write_pid_file()
            
            # Backup saves if enabled
            self.backup_save_files()

            # Mount ISO if configured
            self.mount_iso()

            # Execute launch sequence
            self.executor.execute('launch_sequence')
            
            # Run the game
            self.run_game()
            
            # Execute exit sequence
            self.executor.execute('exit_sequence')
            
        except Exception as e:
            self.show_message(f"Error: {e}")
        finally:
            # Final cleanup to ensure system state is restored
            self.executor.ensure_cleanup()
            self.unmount_iso()
            if self.use_kill_list:
                self.kill_processes_in_list()
            self.show_message("Exiting launcher")
    
    # Helper methods
    def split_path(self, path):
        """Split a path into components (similar to SplitPath in AHK)"""
        p = Path(path)
        return str(p), str(p.parent), p.suffix.lstrip('.'), p.stem
    
    def run_process(self, cmd: Union[str, List[str]], cwd: Optional[str] = None, wait: bool = False, hide: bool = False) -> Optional[subprocess.Popen]:
        """
        Run a process with the given command in a more robust and secure way.

        Args:
            cmd: The command to run, as a string or a list of arguments.
            cwd: The working directory for the process.
            wait: If True, wait for the process to complete and capture output.
            hide: If True on Windows, create the process with no window.

        Returns:
            A subprocess.Popen object if wait is False and the process starts, otherwise None.
        """
        kwargs = {'cwd': cwd}
        
        # On Windows, we use shlex to safely parse command strings into lists,
        # avoiding shell=True for better security.
        if platform.system() == 'Windows':
            if isinstance(cmd, str):
                cmd_list = shlex.split(cmd)
            else:
                cmd_list = cmd # Assume it's already a list
            
            # Set creation flags for hiding the window
            creation_flags = 0
            if hide:
                creation_flags = subprocess.CREATE_NO_WINDOW
            kwargs['creationflags'] = creation_flags
        else: # For Linux/macOS
            # On non-Windows, shell=True is often more convenient for string commands.
            # For list commands, shell=False is the default and correct way.
            if isinstance(cmd, str):
                kwargs['shell'] = True
            cmd_list = cmd

        try:
            self.show_message(f"Executing: {cmd}")
            
            # If we need to wait, it's better to capture output for debugging.
            if wait:
                # Redirect stdout and stderr to capture output for logging
                process = subprocess.Popen(cmd_list, **kwargs, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = process.communicate() # This also waits for the process to finish
                if process.returncode != 0:
                    # Decode stderr and log it if the process failed
                    error_message = stderr.decode('utf-8', errors='ignore').strip()
                    self.show_message(f"Process '{cmd_list[0]}' exited with error code {process.returncode}: {error_message}")
                    logging.warning(f"Process '{cmd_list}' exited with code {process.returncode}. Stderr: {error_message}")
                return None
            else:
                # For non-waiting processes, don't capture stdout/stderr to avoid pipe buffer deadlocks
                process = subprocess.Popen(cmd_list, **kwargs)
                return process

        except FileNotFoundError:
            self.show_message(f"Error: Command not found for '{str(cmd)}'")
            logging.error(f"Command not found: {cmd}", exc_info=True)
            return None
        except PermissionError:
            self.show_message(f"Error: Permission denied for '{str(cmd)}'. Try running as administrator.")
            logging.error(f"Permission denied for: {cmd}", exc_info=True)
            return None
        except Exception as e:
            self.show_message(f"Error running process '{str(cmd)}': {e}")
            logging.error(f"Failed to run process '{cmd}': {e}", exc_info=True)
            return None
    
    def _on_terminate(self, proc):
        """Callback for psutil.wait_procs to log terminated processes."""
        self.show_message(f"  - Process {proc.name()} (PID: {proc.pid}) terminated.")
        logging.info(f"Process {proc.name()} (PID: {proc.pid}) terminated.")

    def terminate_process_tree(self, proc: psutil.Process, timeout: int = 3):
        """
        Gracefully terminates a process and its entire process tree.
        Tries to terminate, waits for a timeout, then forcefully kills if necessary.
        """
        if not proc or not psutil.pid_exists(proc.pid):
            return

        try:
            proc_name = proc.name()
            self.show_message(f"Terminating process tree for {proc_name} (PID: {proc.pid})...")

            # Get all children of the process before terminating the parent
            children = proc.children(recursive=True)
            all_procs_to_terminate = [proc] + children

            for p in all_procs_to_terminate:
                try:
                    p.terminate()
                except psutil.NoSuchProcess:
                    continue # Process already ended

            # Wait for all processes to terminate
            gone, alive = psutil.wait_procs(all_procs_to_terminate, timeout=timeout, callback=self._on_terminate)

            # If any are still alive, kill them forcefully
            for p in alive:
                try:
                    self.show_message(f"  - Process {p.name()} (PID: {p.pid}) did not exit gracefully. Killing.")
                    p.kill()
                except psutil.NoSuchProcess:
                    continue

        except psutil.NoSuchProcess:
            # This can happen if the process terminates between the pid_exists check and the name() call
            self.show_message(f"Process with PID {proc.pid} no longer exists.")
        except psutil.AccessDenied as e:
            self.show_message(f"Access denied terminating process {proc.pid}: {e}")
            logging.warning(f"Access denied terminating process {proc.pid}: {e}", exc_info=True)
        except Exception as e:
            self.show_message(f"Error terminating process {proc.pid}: {e}")
            logging.error(f"Error terminating process {proc.pid}: {e}", exc_info=True)

    def kill_process_by_name(self, process_name: str, timeout: int = 3):
        """Finds and kills processes by exact name match."""
        if platform.system() != 'Windows':
            return
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'].lower() == process_name.lower():
                self.terminate_process_tree(proc, timeout=timeout)
    
    def kill_processes_in_list(self):
        """Kill processes in the kill list"""
        if not self.use_kill_list or not hasattr(self, 'kill_list'):
            return
        
        for proc_name in self.kill_list:
            self.show_message(f"Killing process from list: {proc_name}")
            self.kill_process_by_name(proc_name)
    
    def write_pid_file(self):
        """Write the current PID to the PID file"""
        config = configparser.ConfigParser()
        
        # Read existing file if it exists
        if os.path.exists(self.curpidf):
            config.read(self.curpidf)
        
        # Ensure sections exist
        if 'Instance' not in config:
            config['Instance'] = {}
        
        # Update PID
        config['Instance']['pid'] = str(self.current_pid)
        config['Instance']['multi_instance'] = str(self.multi_instance)
        
        # Write to file
        with open(self.curpidf, 'w') as f:
            config.write(f)

    def close_splash(self):
        """Close the PyInstaller splash screen if it exists"""
        try:
            import pyi_splash
            if pyi_splash.is_alive():
                pyi_splash.close()
        except ImportError:
            pass

# Entry point
if __name__ == "__main__":
    launcher = GameLauncher()
    launcher.run()
