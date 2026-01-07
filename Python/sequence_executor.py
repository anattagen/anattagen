import os
import platform
import logging

# Conditional imports for Windows-specific features
if platform.system() == 'Windows':
    import win32gui
    import win32con

class SequenceExecutor:
    """Handles the execution of launch and exit sequences for the GameLauncher."""

    def __init__(self, launcher):
        self.launcher = launcher
        self.taskbar_hwnd = None
        self.taskbar_was_hidden = False
        self.running_processes = {}  # To track stoppable processes

        if platform.system() == 'Windows':
            try:
                self.taskbar_hwnd = win32gui.FindWindow("Shell_TrayWnd", None)
            except Exception as e:
                self.launcher.show_message(f"Could not find taskbar: {e}")

        # Map sequence keys to methods
        self.actions = {
            'Controller-Mapper': self.run_controller_mapper,
            'Monitor-Config': self.run_monitor_config_game,
            'No-TB': self.hide_taskbar,
            'Pre1': lambda: self.run_generic_app('pre_launch_app_1', 'pre_launch_app_1_wait'),
            'Pre2': lambda: self.run_generic_app('pre_launch_app_2', 'pre_launch_app_2_wait'),
            'Pre3': lambda: self.run_generic_app('pre_launch_app_3', 'pre_launch_app_3_wait'),
            'Borderless': self.run_borderless,
            'JustAfterLaunch': lambda: self.run_generic_app('just_after_launch_app', 'just_after_launch_wait'),
            'Post1': lambda: self.run_generic_app('post_launch_app_1', 'post_launch_app_1_wait'),
            'Post2': lambda: self.run_generic_app('post_launch_app_2', 'post_launch_app_2_wait'),
            'Post3': lambda: self.run_generic_app('post_launch_app_3', 'post_launch_app_3_wait'),
            'Taskbar': self.show_taskbar,
            'JustBeforeExit': lambda: self.run_generic_app('just_before_exit_app', 'just_before_exit_wait'),
        }

        # Define explicit "off" or "restore" actions for the exit sequence
        self.exit_actions_map = {
            'Controller-Mapper': self.kill_controller_mapper,
            'Monitor-Config': self.run_monitor_config_desktop,
            'Borderless': self.kill_borderless,
        }

    def execute(self, sequence_name):
        """Executes a named sequence from the launcher's configuration."""
        sequence = getattr(self.launcher, sequence_name, [])
        is_exit_sequence = (sequence_name == 'exit_sequence')

        self.launcher.show_message(f"Executing {sequence_name}...")
        for item in sequence:
            item = item.strip()
            if not item:
                continue

            action = None
            # For the exit sequence, check for an explicit "off" action first
            if is_exit_sequence and item in self.exit_actions_map:
                action = self.exit_actions_map.get(item)

            # If no specific exit action, use the general action map
            if not action:
                action = self.actions.get(item)

            if action:
                self.launcher.show_message(f"  - Running: {item}")
                try:
                    action()
                except Exception as e:
                    self.launcher.show_message(f"  - Error executing '{item}': {e}")
                    logging.error(f"Error executing sequence item '{item}': {e}", exc_info=True)
            else:
                self.launcher.show_message(f"  - Unknown action: {item}")

    def run_generic_app(self, app_attr, wait_attr):
        app_path = getattr(self.launcher, app_attr, '')
        wait = getattr(self.launcher, wait_attr, False)
        if app_path and os.path.exists(app_path):
            process = self.launcher.run_process(f'"{app_path}"', wait=wait)
            if process and not wait:
                # Track the process if we don't wait for it to close
                self.running_processes[app_attr] = process

    def run_controller_mapper(self):
        app = self.launcher.controller_mapper_app
        p1 = self.launcher.player1_profile
        p2 = self.launcher.player2_profile

        if not (app and os.path.exists(app) and p1 and os.path.exists(p1)):
            self.launcher.show_message("  - Controller Mapper or P1 Profile not configured/found.")
            return

        mapper_name = os.path.basename(app).lower()
        cmd = None

        if "antimicro" in mapper_name:
            cmd = f'"{app}" --tray --hidden --profile "{p1}"'
            if p2 and os.path.exists(p2):
                cmd += f' --next --profile-controller 2 --profile "{p2}"'
        elif "joyxoff" in mapper_name or "joy2key" in mapper_name or "keysticks" in mapper_name:
            cmd = f'"{app}" -load "{p1}"'

        if cmd:
            process = self.launcher.run_process(cmd)
            if process:
                self.running_processes['controller_mapper'] = process
        else:
            self.launcher.show_message(f"  - Unsupported controller mapper: {mapper_name}")

    def kill_controller_mapper(self):
        """Terminates the tracked controller mapper process."""
        process = self.running_processes.pop('controller_mapper', None)
        if process:
            self.launcher.terminate_process_tree(process)
        # Fallback for safety if the process wasn't tracked
        elif self.launcher.controller_mapper_app and platform.system() == 'Windows':
            self.launcher.kill_process_by_name(os.path.basename(self.launcher.controller_mapper_app))

    def run_monitor_config_game(self):
        tool = self.launcher.multimonitor_tool
        config = self.launcher.mm_game_config
        if tool and config and os.path.exists(tool) and os.path.exists(config):
            self.launcher.run_process(f'"{tool}" /load "{config}"', wait=True)

    def run_monitor_config_desktop(self):
        tool = self.launcher.multimonitor_tool
        config = getattr(self.launcher, 'mm_desktop_config', '')
        if tool and config and os.path.exists(tool) and os.path.exists(config):
            self.launcher.run_process(f'"{tool}" /load "{config}"', wait=True)

    def hide_taskbar(self):
        if self.launcher.hide_taskbar and self.taskbar_hwnd and platform.system() == 'Windows':
            win32gui.ShowWindow(self.taskbar_hwnd, win32con.SW_HIDE)
            self.taskbar_was_hidden = True

    def show_taskbar(self):
        if self.taskbar_hwnd and platform.system() == 'Windows':
            win32gui.ShowWindow(self.taskbar_hwnd, win32con.SW_SHOW)
            self.taskbar_was_hidden = False

    def run_borderless(self):
        # This is handled in run_game to ensure it runs after the game window is created.
        if self.launcher.borderless in ['E', 'K']:
            self.launcher.show_message("  - Borderless windowing will be applied after game launch.")

    def kill_borderless(self):
        """Terminates the borderless windowing application if configured to do so."""
        if self.launcher.terminate_borderless_on_exit:
            # Preferentially kill the tracked process from the launcher
            if self.launcher.borderless_process:
                self.launcher.terminate_process_tree(self.launcher.borderless_process)
                self.launcher.borderless_process = None
            # Fallback to killing by name if it wasn't tracked
            elif self.launcher.borderless_app and platform.system() == 'Windows':
                self.launcher.kill_process_by_name(os.path.basename(self.launcher.borderless_app))

    def ensure_cleanup(self):
        """A final cleanup to restore system state, e.g., show taskbar."""
        if self.taskbar_was_hidden:
            self.show_taskbar()
        self.kill_all_tracked()

    def kill_all_tracked(self):
        """Kills all non-waiting processes started by the executor."""
        if platform.system() != 'Windows':
            return
        self.launcher.show_message("Cleaning up background processes...")
        # Iterate over a copy of the items since the dictionary might be modified
        for name, process in list(self.running_processes.items()):
            self.launcher.terminate_process_tree(process)
        self.running_processes.clear()