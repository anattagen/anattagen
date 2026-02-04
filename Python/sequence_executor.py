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
            'Kill-Game': self.kill_game_process,
            'Kill-List': self.kill_process_list,
            'Controller-Mapper': self.run_controller_mapper_launch,
            'Monitor-Config': self.run_monitor_config_game,
            'No-TB': self.hide_taskbar,
            'Pre1': lambda: self.run_generic_app('pre_launch_app_1', 'pre_launch_app_1_wait', 'pre_launch_app_1_options', 'pre_launch_app_1_arguments'),
            'Pre2': lambda: self.run_generic_app('pre_launch_app_2', 'pre_launch_app_2_wait', 'pre_launch_app_2_options', 'pre_launch_app_2_arguments'),
            'Pre3': lambda: self.run_generic_app('pre_launch_app_3', 'pre_launch_app_3_wait', 'pre_launch_app_3_options', 'pre_launch_app_3_arguments'),
            'Borderless': self.run_borderless,
            'JustAfterLaunch': lambda: self.run_generic_app('just_after_launch_app', 'just_after_launch_wait', 'just_after_launch_options', 'just_after_launch_arguments'),
            'JustBeforeExit': lambda: self.run_generic_app('just_before_exit_app', 'just_before_exit_wait', 'just_before_exit_options', 'just_before_exit_arguments'),
            'Post1': lambda: self.run_generic_app('post_launch_app_1', 'post_launch_app_1_wait', 'post_launch_app_1_options', 'post_launch_app_1_arguments'),
            'Post2': lambda: self.run_generic_app('post_launch_app_2', 'post_launch_app_2_wait', 'post_launch_app_2_options', 'post_launch_app_2_arguments'),
            'Post3': lambda: self.run_generic_app('post_launch_app_3', 'post_launch_app_3_wait', 'post_launch_app_3_options', 'post_launch_app_3_arguments'),
            'Taskbar': self.show_taskbar,
            'Cloud-Sync': self.run_cloud_sync,
            'mount-disc': lambda: self.run_generic_app('disc_mount_app', 'disc_mount_wait', 'disc_mount_options', 'disc_mount_arguments'),
            'Unmount-disc': lambda: self.run_generic_app('disc_unmount_app', 'disc_unmount_wait', 'disc_unmount_options', 'disc_unmount_arguments'),
        }

        # Define explicit "off" or "restore" actions for the exit sequence
        self.exit_actions_map = {
            'Kill-Game': self.kill_game_process,
            'Kill-List': self.kill_process_list,
            'Controller-Mapper': self.run_controller_mapper_exit,
            'Monitor-Config': self.run_monitor_config_desktop,
            'Borderless': self.kill_borderless,
            'Cloud-Sync': self.run_cloud_sync,
            'Unmount-disc': lambda: self.run_generic_app('disc_unmount_app', 'disc_unmount_wait', 'disc_unmount_options', 'disc_unmount_arguments'),
        }

    def execute(self, sequence_name):
        """Executes a named sequence from the launcher's configuration."""
        sequence = getattr(self.launcher, sequence_name, [])
        is_exit_sequence = (sequence_name == 'exit_sequence')

        self.launcher.show_message(f"Executing {sequence_name}...")
        logging.info(f"Executing sequence: {sequence_name}")
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
                logging.info(f"  - Action: {item}")
                try:
                    action()
                except Exception as e:
                    self.launcher.show_message(f"  - Error executing '{item}': {e}")
                    logging.error(f"Error executing sequence item '{item}': {e}", exc_info=True)
            else:
                self.launcher.show_message(f"  - Unknown action: {item}")
                logging.warning(f"Unknown action in sequence: {item}")

    def run_generic_app(self, app_attr, wait_attr, options_attr=None, args_attr=None):
        app_path = self.launcher.resolve_path(getattr(self.launcher, app_attr, ''))
        wait = getattr(self.launcher, wait_attr, False)
        options = getattr(self.launcher, options_attr, '') if options_attr else ''
        args = getattr(self.launcher, args_attr, '') if args_attr else ''

        if app_path and os.path.exists(app_path):
            logging.info(f"Running generic app: {app_path} (Wait: {wait})")
            cmd = f'"{app_path}"'
            if options:
                cmd += f' {options}'
            if args:
                cmd += f' {args}'
            process = self.launcher.run_process(cmd, wait=wait)
            if process and not wait:
                # Track the process if we don't wait for it to close
                self.running_processes[app_attr] = process

    def run_controller_mapper_launch(self):
        self._run_controller_mapper(is_exit=False)

    def run_controller_mapper_exit(self):
        self._run_controller_mapper(is_exit=True)

    def _run_controller_mapper(self, is_exit=False):
        app = self.launcher.resolve_path(getattr(self.launcher, 'controller_mapper_app', ''))
        options = getattr(self.launcher, 'controller_mapper_options', '')
        args = getattr(self.launcher, 'controller_mapper_arguments', '')

        if is_exit:
            # Use MediaCenter profile for exit/restore
            p1 = getattr(self.launcher, 'mediacenter_profile', '')
            p2 = getattr(self.launcher, 'mediacenter_profile', '') # Use same for p2 if needed
        else:
            # Use Game profiles
            p1 = getattr(self.launcher, 'player1_profile', '')
            p2 = getattr(self.launcher, 'player2_profile', '')

        if not (app and os.path.exists(app) and p1 and os.path.exists(p1)):
            self.launcher.show_message("  - Controller Mapper or P1 Profile not configured/found.")
            logging.warning("Controller Mapper or P1 Profile not configured/found.")
            return

        mapper_name = os.path.basename(app).lower()
        cmd = None
        logging.info(f"Starting Controller Mapper: {mapper_name}")

        # Construct command: $mapper $mapperoptions $player1 $mapperarguments $player2
        if "antimicro" in mapper_name:
            cmd = f'"{app}"'
            if options: cmd += f' {options}'
            cmd += f' --tray --hidden --profile "{p1}"'
            if args: cmd += f' {args}'
            if p2 and os.path.exists(p2):
                cmd += f' --next --profile-controller 2 --profile "{p2}"'
        elif "joyxoff" in mapper_name or "joy2key" in mapper_name or "keysticks" in mapper_name:
            cmd = f'"{app}" -load "{p1}"'
            if options: cmd += f' {options}'
            if args: cmd += f' {args}'
        else:
            cmd = f'"{app}"'
            if options: cmd += f' {options}'
            if args: cmd += f' {args}'

        if cmd:
            process = self.launcher.run_process(cmd)
            if process:
                self.running_processes['controller_mapper'] = process
        else:
            self.launcher.show_message(f"  - Unsupported controller mapper: {mapper_name}")
            logging.warning(f"Unsupported controller mapper: {mapper_name}")

    def kill_controller_mapper(self):
        """Terminates the tracked controller mapper process."""
        logging.info("Stopping Controller Mapper...")
        process = self.running_processes.pop('controller_mapper', None)
        if process:
            self.launcher.terminate_process_tree(process)
        # Fallback for safety if the process wasn't tracked
        else:
            app = self.launcher.resolve_path(getattr(self.launcher, 'controller_mapper_app', ''))
            if app and platform.system() == 'Windows':
                self.launcher.kill_process_by_name(os.path.basename(app))

    def run_monitor_config_game(self):
        tool = getattr(self.launcher, 'multimonitor_tool', '')
        config = getattr(self.launcher, 'mm_game_config', '')
        options = getattr(self.launcher, 'multimonitor_options', '')
        args = getattr(self.launcher, 'multimonitor_arguments', '')

        if tool and config and os.path.exists(self.launcher.resolve_path(tool)) and os.path.exists(config):
            logging.info(f"Applying Game Monitor Config: {config}")
            cmd = f'"{tool}"'
            if options: cmd += f' {options}'
            cmd += f' /load "{config}"'
            if args: cmd += f' {args}'
            self.launcher.run_process(cmd, wait=True)

    def run_monitor_config_desktop(self):
        tool = getattr(self.launcher, 'multimonitor_tool', '')
        config = getattr(self.launcher, 'mm_desktop_config', '')
        options = getattr(self.launcher, 'multimonitor_options', '')
        args = getattr(self.launcher, 'multimonitor_arguments', '')

        if tool and config and os.path.exists(self.launcher.resolve_path(tool)) and os.path.exists(config):
            logging.info(f"Applying Desktop Monitor Config: {config}")
            cmd = f'"{tool}"'
            if options: cmd += f' {options}'
            cmd += f' /load "{config}"'
            if args: cmd += f' {args}'
            self.launcher.run_process(cmd, wait=True)

    def hide_taskbar(self):
        hide = getattr(self.launcher, 'hide_taskbar', False)
        if hide and self.taskbar_hwnd and platform.system() == 'Windows':
            logging.info("Hiding Taskbar")
            try:
                win32gui.ShowWindow(self.taskbar_hwnd, win32con.SW_HIDE)
                self.taskbar_was_hidden = True
            except Exception as e:
                self.launcher.show_message(f"Failed to hide taskbar: {e}")
                logging.error(f"Failed to hide taskbar: {e}", exc_info=True)

    def show_taskbar(self):
        if self.taskbar_hwnd and platform.system() == 'Windows':
            logging.info("Showing Taskbar")
            try:
                win32gui.ShowWindow(self.taskbar_hwnd, win32con.SW_SHOW)
                self.taskbar_was_hidden = False
            except Exception as e:
                self.launcher.show_message(f"Failed to show taskbar: {e}")
                logging.error(f"Failed to show taskbar: {e}", exc_info=True)

    def run_borderless(self):
        borderless = getattr(self.launcher, 'borderless', '0')
        app = self.launcher.resolve_path(getattr(self.launcher, 'borderless_app', ''))
        options = getattr(self.launcher, 'borderless_options', '')
        args = getattr(self.launcher, 'borderless_arguments', '')

        if borderless in ['E', 'K'] and app and os.path.exists(app):
            logging.info("Starting Borderless Gaming...")
            cmd = f'"{app}"'
            if options: cmd += f' {options}'
            if args: cmd += f' {args}'
            self.launcher.borderless_process = self.launcher.run_process(cmd)

    def kill_borderless(self):
        """Terminates the borderless windowing application if configured to do so."""
        terminate = getattr(self.launcher, 'terminate_borderless_on_exit', False)
        if terminate:
            logging.info("Terminating Borderless Windowing...")
            # Preferentially kill the tracked process from the launcher
            borderless_process = getattr(self.launcher, 'borderless_process', None)
            if borderless_process:
                self.launcher.terminate_process_tree(borderless_process)
                self.launcher.borderless_process = None
            # Fallback to killing by name if it wasn't tracked
            else:
                app = self.launcher.resolve_path(getattr(self.launcher, 'borderless_app', ''))
                if app and platform.system() == 'Windows':
                    self.launcher.kill_process_by_name(os.path.basename(app))

    def run_cloud_sync(self):
        app = self.launcher.resolve_path(getattr(self.launcher, 'cloud_app', ''))
        options = getattr(self.launcher, 'cloud_app_options', '')
        args = getattr(self.launcher, 'cloud_app_arguments', '')

        if app and os.path.exists(app):
            logging.info("Running Cloud Sync...")
            cmd = f'"{app}"'
            if options: cmd += f' {options}'
            if args: cmd += f' {args}'
            self.launcher.run_process(cmd, wait=True)

    def kill_game_process(self):
        """Kills the game executable process."""
        game_path = getattr(self.launcher, 'game_path', '')
        if game_path:
            exe_name = os.path.basename(game_path)
            logging.info(f"Killing game process: {exe_name}")
            self.launcher.kill_process_by_name(exe_name)

    def kill_process_list(self):
        """Kills processes defined in the kill list."""
        kill_list = getattr(self.launcher, 'kill_list', [])
        if kill_list:
            logging.info("Executing Kill List...")
            self.launcher.kill_processes_in_list()

    def ensure_cleanup(self):
        """A final cleanup to restore system state, e.g., show taskbar."""
        logging.info("Ensuring cleanup...")
        if self.taskbar_was_hidden:
            self.show_taskbar()
        self.kill_all_tracked()

    def kill_all_tracked(self):
        """Kills all non-waiting processes started by the executor."""
        if platform.system() != 'Windows':
            return
        self.launcher.show_message("Cleaning up background processes...")
        logging.info("Cleaning up background processes...")
        # Iterate over a copy of the items since the dictionary might be modified
        for name, process in list(self.running_processes.items()):
            self.launcher.terminate_process_tree(process)
        self.running_processes.clear()