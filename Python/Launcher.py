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
import tempfile
import signal
import psutil
import logging
from pathlib import Path
import winreg
import win32gui
import win32con
import win32process
import win32api
import shlex
from typing import Dict, List, Optional, Tuple, Union
import platform

# Import the new sequence executor
from Python.launcher.sequence_executor import SequenceExecutor

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
        
        self.game_process = None
        self.borderless_process = None

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
        
        # Initialize the sequence executor
        self.executor = SequenceExecutor(self)

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
            self.mm_desktop_config = config.get('Paths', 'MultiMonitorDesktopConfig', fallback='')
        
        # Load options
        if 'Options' in config:
            self.run_as_admin = config.getboolean('Options', 'RunAsAdmin', fallback=False)
            self.hide_taskbar = config.getboolean('Options', 'HideTaskbar', fallback=False)
            self.borderless = config.get('Options', 'Borderless', fallback='0')
            self.use_kill_list = config.getboolean('Options', 'UseKillList', fallback=False)
            self.terminate_borderless_on_exit = config.getboolean('Options', 'TerminateBorderlessOnExit', fallback=False)


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
        
        # If borderless windowing is enabled, run it and track it
        if self.borderless in ['E', 'K'] and self.borderless_app and os.path.exists(self.borderless_app):
            self.borderless_process = self.run_process(f'"{self.borderless_app}"')
        
        # Wait for the game to exit
        if self.game_process:
            self.game_process.wait()

    def run(self):
        """Main execution flow"""
        try:
            # Write current PID to the PID file
            self.write_pid_file()
            
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
