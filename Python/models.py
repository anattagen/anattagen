class AppConfig:
    """Data class to hold all application configuration."""
    def __init__(self):
        # Setup Tab: Main Settings
        self.source_dirs = []
        self.logging_verbosity = "Low"

        # Setup Tab: Element & Application Locations
        self.profiles_dir = ""
        self.launchers_dir = ""
        self.controller_mapper_path = ""
        self.borderless_gaming_path = ""
        self.multi_monitor_tool_path = ""
        self.p1_profile_path = ""
        self.p2_profile_path = ""
        self.mediacenter_profile_path = ""
        self.multimonitor_gaming_path = ""
        self.multimonitor_media_path = ""
        
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

        # Setup Tab: Propagation Status (CEN/LC modes)
        self.deployment_path_modes = {}

        # Setup Tab: Execution Sequences
        self.launch_sequence = []
        self.exit_sequence = []

        # Deployment Tab: General Options
        self.net_check = False
        self.hide_taskbar = False
        self.run_as_admin = False
        self.enable_name_matching = False
        self.steam_json_version = 2

        # Deployment Tab: Creation Options
        self.create_profile_folders = False
        self.create_overwrite_launcher = False
        self.create_overwrite_joystick_profiles = False

        # Other settings not directly on UI
        self.app_directory = ""
