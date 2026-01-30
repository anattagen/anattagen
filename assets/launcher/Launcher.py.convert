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
import platform
import shutil
import tempfile
import signal
import psutil
from pathlib import Path
import winreg
import win32gui
import win32con
import win32process
import win32api
from typing import Dict, List, Optional, Tuple, Union

class GameLauncher:
    def __init__(self):
        # Initialize variables
        self.home = os.path.dirname(os.path.abspath(__file__))
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
        self.exe_list = ""
        self.joymessage = "No joysticks detected"
        self.joycount = 0
        self.mapper_extension = "gamecontroller.amgp"  # Default for antimicrox
        
        # Get command line arguments
        self.parse_arguments()
        
        # Check if we're running as admin
        self.is_admin = self.check_admin()
        
        # Set up message display
        self.setup_message_display()
        
        # Check for other instances
        if not self.check_instances():
            sys.exit(0)
        
        # Load configuration
        self.load_config()
        
        # Initialize joystick detection
        self.detect_joysticks()

    def parse_arguments(self):
        """Parse command line arguments"""
        if len(sys.argv) > 1:
            self.plink = sys.argv[1]
            
            # Get file extension
            _, self.scpath, self.scextn, self.game_name = self.split_path(self.plink)
            
            # Display message
            self.show_message(f"Launching: {self.plink}")
        else:
            self.show_message("No Item Detected")
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
        # For now, just use print. In a full implementation, 
        # this could be a small GUI window or system notification
        pass
    
    def show_message(self, message):
        """Show a message to the user"""
        print(message)
        # In a full implementation, this could update a GUI or show a notification
    
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
        
        config = configparser.ConfigParser()
        config.read(game_ini)
        
        # Load game information
        if 'Game' in config:
            self.game_path = config.get('Game', 'Executable', fallback='')
            self.game_dir = config.get('Game', 'Directory', fallback='')
            self.game_name = config.get('Game', 'Name', fallback=self.game_name)
        
        # Load paths
        if 'Paths' in config:
            self.controller_mapper_app = config.get('Paths', 'ControllerMapperApp', fallback='')
            self.borderless_app = config.get('Paths', 'BorderlessWindowingApp', fallback='')
            self.multimonitor_tool = config.get('Paths', 'MultiMonitorTool', fallback='')
            self.player1_profile = config.get('Paths', 'Player1Profile', fallback='')
            self.player2_profile = config.get('Paths', 'Player2Profile', fallback='')
            self.mm_game_config = config.get('Paths', 'MultiMonitorGamingConfig', fallback='')
        
        # Load options
        if 'Options' in config:
            self.run_as_admin = config.get('Options', 'RunAsAdmin', fallback='0') == '1'
            self.hide_taskbar = config.get('Options', 'HideTaskbar', fallback='0') == '1'
            self.borderless = config.get('Options', 'Borderless', fallback='0')
            self.use_kill_list = config.get('Options', 'UseKillList', fallback='0') == '1'
        
        # Load pre-launch apps
        if 'PreLaunch' in config:
            self.pre_launch_app_1 = config.get('PreLaunch', 'App1', fallback='')
            self.pre_launch_app_2 = config.get('PreLaunch', 'App2', fallback='')
            self.pre_launch_app_3 = config.get('PreLaunch', 'App3', fallback='')
            self.pre_launch_app_1_wait = config.get('PreLaunch', 'App1Wait', fallback='0') == '1'
            self.pre_launch_app_2_wait = config.get('PreLaunch', 'App2Wait', fallback='0') == '1'
            self.pre_launch_app_3_wait = config.get('PreLaunch', 'App3Wait', fallback='0') == '1'
        
        # Load post-launch apps
        if 'PostLaunch' in config:
            self.post_launch_app_1 = config.get('PostLaunch', 'App1', fallback='')
            self.post_launch_app_2 = config.get('PostLaunch', 'App2', fallback='')
            self.post_launch_app_3 = config.get('PostLaunch', 'App3', fallback='')
            self.post_launch_app_1_wait = config.get('PostLaunch', 'App1Wait', fallback='0') == '1'
            self.post_launch_app_2_wait = config.get('PostLaunch', 'App2Wait', fallback='0') == '1'
            self.post_launch_app_3_wait = config.get('PostLaunch', 'App3Wait', fallback='0') == '1'
            self.just_after_launch_app = config.get('PostLaunch', 'JustAfterLaunchApp', fallback='')
            self.just_before_exit_app = config.get('PostLaunch', 'JustBeforeExitApp', fallback='')
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
    
    def run_pre_launch_apps(self):
        """Run pre-launch applications"""
        self.show_message("Running pre-launch applications")
        
        # Run pre-launch app 1
        if self.pre_launch_app_1 and os.path.exists(self.pre_launch_app_1):
            self.run_process(self.pre_launch_app_1, wait=self.pre_launch_app_1_wait)
        
        # Run pre-launch app 2
        if self.pre_launch_app_2 and os.path.exists(self.pre_launch_app_2):
            self.run_process(self.pre_launch_app_2, wait=self.pre_launch_app_2_wait)
        
        # Run pre-launch app 3
        if self.pre_launch_app_3 and os.path.exists(self.pre_launch_app_3):
            self.run_process(self.pre_launch_app_3, wait=self.pre_launch_app_3_wait)
        
        # Set up multi-monitor configuration if specified
        if self.multimonitor_tool and self.mm_game_config and os.path.exists(self.multimonitor_tool) and os.path.exists(self.mm_game_config):
            self.run_process(f'"{self.multimonitor_tool}" /load "{self.mm_game_config}"', wait=True)
        
        # Set up controller mapper if specified
        if self.controller_mapper_app and self.player1_profile and os.path.exists(self.controller_mapper_app) and os.path.exists(self.player1_profile):
            # Determine which mapper we're using
            mapper_name = os.path.basename(self.controller_mapper_app).lower()
            
            if "antimicro" in mapper_name:
                # For AntiMicroX
                cmd = f'"{self.controller_mapper_app}" --tray --hidden --profile "{self.player1_profile}"'
                if self.player2_profile and os.path.exists(self.player2_profile):
                    cmd += f' --next --profile-controller 2 --profile "{self.player2_profile}"'
                self.run_process(cmd)
            elif "joyxoff" in mapper_name:
                # For JoyXoff
                self.run_process(f'"{self.controller_mapper_app}" -load "{self.player1_profile}"')
            elif "joy2key" in mapper_name:
                # For Joy2Key
                self.run_process(f'"{self.controller_mapper_app}" -load "{self.player1_profile}"')
            elif "keysticks" in mapper_name:
                # For KeySticks
                self.run_process(f'"{self.controller_mapper_app}" -load "{self.player1_profile}"')
    
    def run_game(self):
        """Run the main game executable"""
        self.show_message(f"Launching game: {self.game_name}")
        
        # Prepare the command
        if not self.game_path:
            self.game_path = self.plink
        
        # Get the game directory
        if not self.game_dir:
            self.game_dir = os.path.dirname(self.game_path)
        
        # Run the game
        if self.run_as_admin and platform.system() == 'Windows' and not self.is_admin:
            # Use PowerShell to run as admin
            cmd = f'powershell -Command "Start-Process \'{self.game_path}\' -Verb RunAs"'
            self.game_process = self.run_process(cmd, cwd=self.game_dir)
        else:
            self.game_process = self.run_process(f'"{self.game_path}"', cwd=self.game_dir)
        
        # Run just after launch app if specified
        if self.just_after_launch_app and os.path.exists(self.just_after_launch_app):
            self.run_process(self.just_after_launch_app, wait=self.just_after_launch_wait)
        
        # If borderless windowing is enabled, run it
        if self.borderless in ['E', 'K'] and self.borderless_app and os.path.exists(self.borderless_app):
            self.run_process(self.borderless_app)
        
        # Wait for the game to exit
        if self.game_process:
            self.game_process.wait()
    
    def run_post_launch_apps(self):
        """Run post-launch applications"""
        self.show_message("Running post-launch applications")
        
        # Run just before exit app if specified
        if self.just_before_exit_app and os.path.exists(self.just_before_exit_app):
            self.run_process(self.just_before_exit_app, wait=self.just_before_exit_wait)
        
        # Kill borderless windowing if specified
        if self.borderless == 'K' and self.borderless_app:
            self.kill_process(os.path.basename(self.borderless_app))
        
        # Run post-launch app 1
        if self.post_launch_app_1 and os.path.exists(self.post_launch_app_1):
            self.run_process(self.post_launch_app_1, wait=self.post_launch_app_1_wait)
        
        # Run post-launch app 2
        if self.post_launch_app_2 and os.path.exists(self.post_launch_app_2):
            self.run_process(self.post_launch_app_2, wait=self.post_launch_app_2_wait)
        
        # Run post-launch app 3
        if self.post_launch_app_3 and os.path.exists(self.post_launch_app_3):
            self.run_process(self.post_launch_app_3, wait=self.post_launch_app_3_wait)
    
    def cleanup(self):
        """Clean up processes and restore settings"""
        self.show_message("Cleaning up")
        
        # Kill controller mapper if running
        if self.controller_mapper_app:
            self.kill_process(os.path.basename(self.controller_mapper_app))
        
        # Restore multi-monitor configuration if needed
        # This would typically restore the desktop monitor configuration
        
        # Kill any remaining processes in the kill list if enabled
        if self.use_kill_list:
            self.kill_processes_in_list()
    
    def run(self):
        """Main execution flow"""
        try:
            # Write current PID to the PID file
            self.write_pid_file()
            
            # Run pre-launch applications
            self.run_pre_launch_apps()
            
            # Run the game
            self.run_game()
            
            # Run post-launch applications
            self.run_post_launch_apps()
            
            # Clean up
            self.cleanup()
            
        except Exception as e:
            self.show_message(f"Error: {e}")
        finally:
            self.show_message("Exiting launcher")
    
    # Helper methods
    def split_path(self, path):
        """Split a path into components (similar to SplitPath in AHK)"""
        p = Path(path)
        return str(p), str(p.parent), p.suffix.lstrip('.'), p.stem
    
    def run_process(self, cmd, cwd=None, wait=False, hide=False):
        """Run a process with the given command"""
        try:
            # Set up process creation flags
            creation_flags = 0
            if platform.system() == 'Windows' and hide:
                creation_flags = subprocess.CREATE_NO_WINDOW
            
            # Run the process
            process = subprocess.Popen(
                cmd, 
                cwd=cwd, 
                shell=True, 
                creationflags=creation_flags if platform.system() == 'Windows' else 0
            )
            
            # Wait for the process to complete if requested
            if wait:
                process.wait()
                return None
            
            return process
        except Exception as e:
            self.show_message(f"Error running process: {e}")
            return None
    
    def kill_process(self, process_name):
        """Kill a process by name"""
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                if process_name.lower() in proc.info['name'].lower():
                    proc.terminate()
                    time.sleep(1)
                    if proc.is_running():
                        proc.kill()
        except Exception as e:
            self.show_message(f"Error killing process {process_name}: {e}")
    
    def kill_processes_in_list(self):
        """Kill processes in the kill list"""
        # This would be implemented based on your specific kill list logic
        pass
    
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

# Entry point
if __name__ == "__main__":
    launcher = GameLauncher()
    launcher.run()
