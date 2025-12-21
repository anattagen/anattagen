import configparser
import os
import logging
from Python.models import AppConfig
from Python import constants

CONFIG_FILE = os.path.join(constants.APP_ROOT_DIR, "config.ini")

def load_configuration(config_model: AppConfig):
    """
    Loads configuration from config.ini into the AppConfig data model.
    If no config exists, runs first-time setup.
    """
    config = configparser.ConfigParser()
    
    if not os.path.exists(CONFIG_FILE):
        logging.info(f"Configuration file '{CONFIG_FILE}' not found. Running first-time setup...")
        
        # Import and run first-time setup
        from Python.first_run_init import run_first_time_setup
        run_first_time_setup(config_model)
        
        # Save the auto-detected configuration
        save_configuration(config_model)
        return

    try:
        config.read(CONFIG_FILE, encoding='utf-8')

        # --- Main Settings ---
        if config.has_section("MainSettings"):
            config_model.source_dirs = [d for d in config.get("MainSettings", "SourceDirs", fallback="").splitlines() if d]
            config_model.excluded_dirs = [d for d in config.get("MainSettings", "ExcludedDirs", fallback="").splitlines() if d]
            config_model.logging_verbosity = config.get("MainSettings", "LoggingVerbosity", fallback="Low")
            config_model.app_font = config.get("MainSettings", "AppFont", fallback="System")
            config_model.app_theme = config.get("MainSettings", "AppTheme", fallback="Default")
            config_model.font_size = config.getint("MainSettings", "FontSize", fallback=10)
            config_model.game_managers_present = config.get("MainSettings", "GameManagersPresent", fallback="None")
            config_model.exclude_selected_manager_games = config.getboolean("MainSettings", "ExcludeSelectedManagerGames", fallback=False)

        # --- Paths ---
        if config.has_section("Paths"):
            config_model.profiles_dir = config.get("Paths", "ProfilesDir", fallback="")
            config_model.launchers_dir = config.get("Paths", "LaunchersDir", fallback="")
            config_model.controller_mapper_path = config.get("Paths", "ControllerMapperPath", fallback="")
            config_model.borderless_gaming_path = config.get("Paths", "BorderlessGamingPath", fallback="")
            config_model.multi_monitor_tool_path = config.get("Paths", "MultiMonitorToolPath", fallback="")
            config_model.p1_profile_path = config.get("Paths", "P1ProfilePath", fallback="")
            config_model.p2_profile_path = config.get("Paths", "P2ProfilePath", fallback="")
            config_model.mediacenter_profile_path = config.get("Paths", "MediacenterProfilePath", fallback="")
            config_model.multimonitor_gaming_path = config.get("Paths", "MultimonitorGamingPath", fallback="")
            config_model.multimonitor_media_path = config.get("Paths", "MultimonitorMediaPath", fallback="")
            config_model.steam_json_path = config.get("Paths", "SteamJsonPath", fallback="")
            config_model.filtered_steam_cache_path = config.get("Paths", "FilteredSteamCachePath", fallback="")
            config_model.just_after_launch_path = config.get("Paths", "JustAfterLaunchPath", fallback="")
            config_model.just_before_exit_path = config.get("Paths", "JustBeforeExitPath", fallback="")
            config_model.pre1_path = config.get("Paths", "Pre1Path", fallback="")
            config_model.pre2_path = config.get("Paths", "Pre2Path", fallback="")
            config_model.pre3_path = config.get("Paths", "Pre3Path", fallback="")
            config_model.post1_path = config.get("Paths", "Post1Path", fallback="")
            config_model.post2_path = config.get("Paths", "Post2Path", fallback="")
            config_model.post3_path = config.get("Paths", "Post3Path", fallback="")

        # --- Propagation Modes ---
        if config.has_section("PropagationModes"):
            for key in config.options("PropagationModes"):
                config_model.deployment_path_modes[key] = config.get("PropagationModes", key)

        # --- Sequences ---
        if config.has_section("Sequences"):
            launch_seq = config.get("Sequences", "LaunchSequence", fallback="")
            config_model.launch_sequence = [s for s in launch_seq.split(',') if s]
            exit_seq = config.get("Sequences", "ExitSequence", fallback="")
            config_model.exit_sequence = [s for s in exit_seq.split(',') if s]

        # --- Deployment ---
        if config.has_section("Deployment"):
            config_model.net_check = config.getboolean("Deployment", "NetCheck", fallback=False)
            config_model.hide_taskbar = config.getboolean("Deployment", "HideTaskbar", fallback=False)
            config_model.run_as_admin = config.getboolean("Deployment", "RunAsAdmin", fallback=False)
            config_model.enable_name_matching = config.getboolean("Deployment", "EnableNameMatching", fallback=False)
            config_model.steam_json_version = config.getint("Deployment", "SteamJSONVersion", fallback=2)
            config_model.create_profile_folders = config.getboolean("Deployment", "CreateProfileFolders", fallback=False)
            config_model.create_overwrite_launcher = config.getboolean("Deployment", "CreateOverwriteLauncher", fallback=False)
            config_model.create_overwrite_joystick_profiles = config.getboolean("Deployment", "CreateOverwriteJoystickProfiles", fallback=False)
            config_model.use_kill_list = config.getboolean("Deployment", "UseKillList", fallback=False)
            config_model.enable_launcher = config.getboolean("Deployment", "EnableLauncher", fallback=False)
            config_model.apply_mapper_profiles = config.getboolean("Deployment", "ApplyMapperProfiles", fallback=False)
            config_model.enable_borderless_windowing = config.getboolean("Deployment", "EnableBorderlessWindowing", fallback=False)
            config_model.terminate_borderless_on_exit = config.getboolean("Deployment", "TerminateBorderlessOnExit", fallback=False)

        # --- Default Enabled States ---
        if config.has_section("DefaultEnabledStates") and config.options("DefaultEnabledStates"):
            for key, value in config.items("DefaultEnabledStates"):
                config_model.defaults[key] = value.lower() in ('true', '1', 'yes', 'on')
        else:
            # Set default enabled states if section doesn't exist or is empty
            config_model.defaults = {
                'controller_mapper_enabled': True,
                'borderless_windowing_enabled': True,
                'multi_monitor_app_enabled': True,
                'just_after_launch_enabled': True,
                'just_before_exit_enabled': True,
                'pre_1_enabled': True,
                'post_1_enabled': True,
                'pre_2_enabled': True,
                'post_2_enabled': True,
                'pre_3_enabled': True,
                'post_3_enabled': True,
            }

        # --- Default Run-Wait States ---
        if config.has_section("DefaultRunWaitStates") and config.options("DefaultRunWaitStates"):
            for key, value in config.items("DefaultRunWaitStates"):
                config_model.run_wait_states[key] = value.lower() in ('true', '1', 'yes', 'on')
        else:
            # Set default run-wait states if section doesn't exist or is empty
            config_model.run_wait_states = {
                'controller_mapper_run_wait': True,
                'borderless_windowing_run_wait': True,
                'multi_monitor_app_run_wait': True,
                'just_after_launch_run_wait': False,
                'just_before_exit_run_wait': True,
                'pre_1_run_wait': True,
                'post_1_run_wait': True,
                'pre_2_run_wait': True,
                'post_2_run_wait': True,
                'pre_3_run_wait': True,
                'post_3_run_wait': True,
            }

    except Exception as e:
        logging.error(f"Error reading configuration file '{CONFIG_FILE}': {e}")

def save_configuration(config_model: AppConfig):
    """
    Saves the state of the AppConfig data model to config.ini.
    """
    config = configparser.ConfigParser()

    # --- Main Settings ---
    config.add_section("MainSettings")
    config.set("MainSettings", "SourceDirs", "\n".join(config_model.source_dirs))
    config.set("MainSettings", "ExcludedDirs", "\n".join(config_model.excluded_dirs))
    config.set("MainSettings", "LoggingVerbosity", config_model.logging_verbosity)
    config.set("MainSettings", "AppFont", config_model.app_font)
    config.set("MainSettings", "AppTheme", config_model.app_theme)
    config.set("MainSettings", "FontSize", str(config_model.font_size))
    config.set("MainSettings", "GameManagersPresent", config_model.game_managers_present)
    config.set("MainSettings", "ExcludeSelectedManagerGames", str(config_model.exclude_selected_manager_games))

    # --- Paths ---
    config.add_section("Paths")
    config.set("Paths", "ProfilesDir", config_model.profiles_dir)
    config.set("Paths", "LaunchersDir", config_model.launchers_dir)
    config.set("Paths", "ControllerMapperPath", config_model.controller_mapper_path)
    config.set("Paths", "BorderlessGamingPath", config_model.borderless_gaming_path)
    config.set("Paths", "MultiMonitorToolPath", config_model.multi_monitor_tool_path)
    config.set("Paths", "P1ProfilePath", config_model.p1_profile_path)
    config.set("Paths", "P2ProfilePath", config_model.p2_profile_path)
    config.set("Paths", "MediacenterProfilePath", config_model.mediacenter_profile_path)
    config.set("Paths", "MultimonitorGamingPath", config_model.multimonitor_gaming_path)
    config.set("Paths", "MultimonitorMediaPath", config_model.multimonitor_media_path)
    config.set("Paths", "SteamJsonPath", config_model.steam_json_path)
    config.set("Paths", "FilteredSteamCachePath", config_model.filtered_steam_cache_path)
    config.set("Paths", "JustAfterLaunchPath", config_model.just_after_launch_path)
    config.set("Paths", "JustBeforeExitPath", config_model.just_before_exit_path)
    config.set("Paths", "Pre1Path", config_model.pre1_path)
    config.set("Paths", "Pre2Path", config_model.pre2_path)
    config.set("Paths", "Pre3Path", config_model.pre3_path)
    config.set("Paths", "Post1Path", config_model.post1_path)
    config.set("Paths", "Post2Path", config_model.post2_path)
    config.set("Paths", "Post3Path", config_model.post3_path)

    # --- Propagation Modes ---
    config.add_section("PropagationModes")
    for key, value in config_model.deployment_path_modes.items():
        config.set("PropagationModes", key, value)

    # --- Sequences ---
    config.add_section("Sequences")
    config.set("Sequences", "LaunchSequence", ",".join(config_model.launch_sequence))
    config.set("Sequences", "ExitSequence", ",".join(config_model.exit_sequence))

    # --- Deployment ---
    config.add_section("Deployment")
    config.set("Deployment", "NetCheck", str(config_model.net_check))
    config.set("Deployment", "HideTaskbar", str(config_model.hide_taskbar))
    config.set("Deployment", "RunAsAdmin", str(config_model.run_as_admin))
    config.set("Deployment", "EnableNameMatching", str(config_model.enable_name_matching))
    config.set("Deployment", "SteamJSONVersion", str(config_model.steam_json_version))
    config.set("Deployment", "CreateProfileFolders", str(config_model.create_profile_folders))
    config.set("Deployment", "CreateOverwriteLauncher", str(config_model.create_overwrite_launcher))
    config.set("Deployment", "CreateOverwriteJoystickProfiles", str(config_model.create_overwrite_joystick_profiles))
    config.set("Deployment", "UseKillList", str(config_model.use_kill_list))
    config.set("Deployment", "EnableLauncher", str(config_model.enable_launcher))
    config.set("Deployment", "ApplyMapperProfiles", str(config_model.apply_mapper_profiles))
    config.set("Deployment", "EnableBorderlessWindowing", str(config_model.enable_borderless_windowing))
    config.set("Deployment", "TerminateBorderlessOnExit", str(config_model.terminate_borderless_on_exit))

    # --- Default Enabled States ---
    config.add_section("DefaultEnabledStates")
    for key, value in config_model.defaults.items():
        config.set("DefaultEnabledStates", key, str(value))

    # --- Default Run-Wait States ---
    config.add_section("DefaultRunWaitStates")
    for key, value in config_model.run_wait_states.items():
        config.set("DefaultRunWaitStates", key, str(value))

    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as configfile:
            config.write(configfile)
        logging.info(f"Configuration saved to '{CONFIG_FILE}'.")
    except Exception as e:
        logging.error(f"Error saving configuration file '{CONFIG_FILE}': {e}")
