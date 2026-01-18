class AppConfig:
    """Data class to hold all application configuration."""
    def __init__(self):
        # Setup Tab: Main Settings
        self.source_dirs = []
        self.excluded_dirs = []
        self.logging_verbosity = "Low"
        self.game_managers_present = "None"
        self.exclude_selected_manager_games = False

        # Setup Tab: Element & Application Locations
        self.profiles_dir = ""
        self.launchers_dir = ""
        self.launcher_executable = ""
        self.controller_mapper_path = ""
        self.borderless_gaming_path = ""
        self.multi_monitor_tool_path = ""
        self.p1_profile_path = ""
        self.p2_profile_path = ""
        self.mediacenter_profile_path = ""
        self.multimonitor_gaming_path = ""
        self.multimonitor_media_path = ""
        self.steam_json_path = ""
        self.filtered_steam_cache_path = ""
        
        # Pre/Post launch apps
        self.pre1_path = ""
        self.pre2_path = ""
        self.pre3_path = ""
        self.post1_path = ""
        self.post2_path = ""
        self.post3_path = ""
        
        # Just Before/After launch apps
        self.just_after_launch_path = ""
        self.just_before_exit_path = ""

        # App Options & Arguments
        self.controller_mapper_path_options = ""
        self.controller_mapper_path_arguments = ""
        self.borderless_gaming_path_options = ""
        self.borderless_gaming_path_arguments = ""
        self.multi_monitor_tool_path_options = ""
        self.multi_monitor_tool_path_arguments = ""
        
        self.just_after_launch_path_options = ""
        self.just_after_launch_path_arguments = ""
        self.just_before_exit_path_options = ""
        self.just_before_exit_path_arguments = ""
        
        self.pre1_path_options = ""
        self.pre1_path_arguments = ""
        self.pre2_path_options = ""
        self.pre2_path_arguments = ""
        self.pre3_path_options = ""
        self.pre3_path_arguments = ""
        
        self.post1_path_options = ""
        self.post1_path_arguments = ""
        self.post2_path_options = ""
        self.post2_path_arguments = ""
        self.post3_path_options = ""
        self.post3_path_arguments = ""
        self.launcher_executable_options = ""
        self.launcher_executable_arguments = ""

        # Setup Tab: Propagation Status (CEN/LC modes)
        self.deployment_path_modes = {}
        
        # CEN/LC states for profile paths
        self.p1_profile_mode = "CEN"  # or "LC"
        self.p2_profile_mode = "CEN"
        self.mediacenter_profile_mode = "CEN"
        self.multimonitor_gaming_mode = "CEN"
        self.multimonitor_media_mode = "CEN"

        # Setup Tab: Appearance
        self.app_font = "System"
        self.app_theme = "Dark"
        self.font_size = 10
        self.editor_page_size = 150

        # Setup Tab: Execution Sequences
        self.launch_sequence = []
        self.exit_sequence = []

        # Deployment Tab: General Options
        self.download_game_json = False
        self.hide_taskbar = False
        self.run_as_admin = False
        self.enable_name_matching = False
        self.steam_json_version = 2
        self.use_kill_list = False
        self.terminate_borderless_on_exit = False

        # Deployment Tab: Creation Options
        self.create_overwrite_joystick_profiles = False

        # Enable toggles for applications defined in Setup -> Applications
        self.enable_controller_mapper = False
        self.enable_borderless_app = False
        self.enable_multimonitor_app = False
        self.enable_after_launch_app = False
        self.enable_before_exit_app = False
        self.enable_pre1 = False
        self.enable_pre2 = False
        self.enable_pre3 = False
        self.enable_post1 = False
        self.enable_post2 = False
        self.enable_post3 = False

        # Other settings not directly on UI
        self.app_directory = ""

        # Default enabled states for various features
        self.defaults = {}

        # Overwrite states for paths (Deployment Tab -> Creation)
        self.overwrite_states = {}

        # Default run-wait states for various features
        self.run_wait_states = {}
