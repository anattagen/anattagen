import configparser
import os
from PyQt6.QtWidgets import QFileDialog, QComboBox, QCheckBox, QLineEdit

def to_snake_case(name):
    """Convert a string to snake_case format"""
    import re
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'[\s-]+(?=[\w])', '_', name.strip()).lower()
    name = re.sub(r'\W', '', name)
    return name

def parse_ini_file(file_path: str) -> configparser.ConfigParser | None:
    """Parse an INI configuration file and return the parsed config"""
    config = configparser.ConfigParser()
    config.optionxform = str  # Preserve key case
    try:
        if not config.read(file_path, encoding='utf-8'):

            return None

        return config
    except Exception as e:

        return None

def gather_current_configuration(main_window) -> configparser.ConfigParser:
    """Gather current UI configuration into a ConfigParser object"""
    config = configparser.ConfigParser()
    config.optionxform = str  # Preserve case for keys
    
    # Initialize sections
    config["Current Settings"] = {}
    config["Element Locations"] = {}
    config["App Locations"] = {}
    config["Deployment Options"] = {}  # Section for deployment options
    
    # Get the app's root directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_root_dir = os.path.dirname(os.path.dirname(script_dir))
    
    # Set app_directory
    config["Current Settings"]["app_directory"] = app_root_dir

    # --- Setup Tab --- 
    source_dirs = [main_window.source_dirs_combo.itemText(i) for i in range(main_window.source_dirs_combo.count())]
    config["Current Settings"]["source_directories"] = "|".join(source_dirs)
    exclude_items = [main_window.exclude_items_combo.itemText(i) for i in range(main_window.exclude_items_combo.count())]
    config["Current Settings"]["exclude_items"] = "|".join(exclude_items)
    config["Current Settings"]["game_managers_present"] = main_window.other_managers_combo.currentText()
    config["Current Settings"]["exclude_selected_manager_games"] = str(main_window.exclude_manager_checkbox.isChecked())
    config["Current Settings"]["logging_verbosity"] = main_window.logging_verbosity_combo.currentText()

    # --- Save CEN/LC options ---
    # Check if deployment_path_options exists
    if hasattr(main_window, 'deployment_path_options'):

        for path_key, radio_group in main_window.deployment_path_options.items():
            checked_button = radio_group.checkedButton()
            if checked_button:
                mode = checked_button.text()

                config["Deployment Options"][f"{path_key}_mode"] = mode

    # --- Element Locations ---
    if hasattr(main_window, 'profiles_dir_edit'):
        config["Element Locations"]["profiles_directory"] = main_window.profiles_dir_edit.text()
    if hasattr(main_window, 'launchers_dir_edit'):
        config["Element Locations"]["launchers_directory"] = main_window.launchers_dir_edit.text()
    if hasattr(main_window, 'p1_profile_edit'):
        config["Element Locations"]["player_1_profile_file"] = main_window.p1_profile_edit.text()
    if hasattr(main_window, 'p2_profile_edit'):
        config["Element Locations"]["player_2_profile_file"] = main_window.p2_profile_edit.text()
    if hasattr(main_window, 'mediacenter_profile_edit'):
        config["Element Locations"]["mediacenter_desktop_profile_file"] = main_window.mediacenter_profile_edit.text()
    if hasattr(main_window, 'multimonitor_gaming_config_edit'):
        config["Element Locations"]["multimonitor_gaming_config_file"] = main_window.multimonitor_gaming_config_edit.text()
    if hasattr(main_window, 'multimonitor_media_config_edit'):
        config["Element Locations"]["multimonitor_media_desktop_config_file"] = main_window.multimonitor_media_config_edit.text()
    
    # Convert to string explicitly
    config["Element Locations"]["steam_json_path"] = str(getattr(main_window, 'steam_json_file_path', ''))
    config["Element Locations"]["filtered_steam_cache_path"] = str(getattr(main_window, 'filtered_steam_cache_file_path', ''))

    # --- App Locations ---
    if hasattr(main_window, 'controller_mapper_app_line_edit'):
        config["App Locations"]["controller_mapper_app"] = main_window.controller_mapper_app_line_edit.text()
    if hasattr(main_window, 'borderless_app_line_edit'):
        config["App Locations"]["borderless_windowing_app"] = main_window.borderless_app_line_edit.text()
    if hasattr(main_window, 'multimonitor_app_line_edit'):
        config["App Locations"]["multi_monitor_app"] = main_window.multimonitor_app_line_edit.text()
    
    if hasattr(main_window, 'pre_launch_app_line_edits'):
        for i, le in enumerate(main_window.pre_launch_app_line_edits):
            config["App Locations"][f"pre_launch_app_{i+1}"] = le.text()
    
    if hasattr(main_window, 'post_launch_app_line_edits'):
        for i, le in enumerate(main_window.post_launch_app_line_edits):
            config["App Locations"][f"post_launch_app_{i+1}"] = le.text()
    
    if hasattr(main_window, 'after_launch_app_line_edit'):
        config["App Locations"]["just_after_launch_app"] = main_window.after_launch_app_line_edit.text()
    
    if hasattr(main_window, 'before_exit_app_line_edit'):
        config["App Locations"]["just_before_exit_app"] = main_window.before_exit_app_line_edit.text()
    
    if hasattr(main_window, 'after_launch_run_wait_checkbox'):
        config["App Locations"]["just_after_launch_app_run_wait"] = str(main_window.after_launch_run_wait_checkbox.isChecked())
    
    if hasattr(main_window, 'before_exit_run_wait_checkbox'):
        config["App Locations"]["just_before_exit_app_run_wait"] = str(main_window.before_exit_run_wait_checkbox.isChecked())
    
    if hasattr(main_window, 'pre_launch_run_wait_checkboxes'):
        for i, cb in enumerate(main_window.pre_launch_run_wait_checkboxes):
            config["App Locations"][f"pre_launch_app_{i+1}_run_wait"] = str(cb.isChecked())
    
    if hasattr(main_window, 'post_launch_run_wait_checkboxes'):
        for i, cb in enumerate(main_window.post_launch_run_wait_checkboxes):
            config["App Locations"][f"post_launch_app_{i+1}_run_wait"] = str(cb.isChecked())

    # --- Deployment Options ---
    if hasattr(main_window, 'net_check_checkbox'):
        config["Current Settings"]["deployment_net_check"] = str(main_window.net_check_checkbox.isChecked())
    if hasattr(main_window, 'name_check_checkbox'):
        config["Current Settings"]["deployment_name_check"] = str(main_window.name_check_checkbox.isChecked())
    if hasattr(main_window, 'create_profile_folders_checkbox'):
        config["Current Settings"]["deployment_create_profile_folders"] = str(main_window.create_profile_folders_checkbox.isChecked())
    if hasattr(main_window, 'use_kill_list_checkbox'):
        config["Current Settings"]["deployment_use_kill_list"] = str(main_window.use_kill_list_checkbox.isChecked())
    if hasattr(main_window, 'run_as_admin_checkbox'):
        config["Current Settings"]["deployment_run_as_admin"] = str(main_window.run_as_admin_checkbox.isChecked())
    if hasattr(main_window, 'hide_taskbar_checkbox'):
        config["Current Settings"]["deployment_hide_taskbar"] = str(main_window.hide_taskbar_checkbox.isChecked())
    if hasattr(main_window, 'enable_launcher_checkbox'):
        config["Current Settings"]["deployment_enable_launcher"] = str(main_window.enable_launcher_checkbox.isChecked())
    if hasattr(main_window, 'apply_mapper_profiles_checkbox'):
        config["Current Settings"]["deployment_apply_mapper_profiles"] = str(main_window.apply_mapper_profiles_checkbox.isChecked())
    if hasattr(main_window, 'enable_borderless_windowing_checkbox'):
        config["Current Settings"]["deployment_enable_borderless_windowing"] = str(main_window.enable_borderless_windowing_checkbox.isChecked())
    if hasattr(main_window, 'terminate_bw_on_exit_checkbox'):
        config["Current Settings"]["deployment_terminate_borderless_on_exit"] = str(main_window.terminate_bw_on_exit_checkbox.isChecked())

    return config

def save_sequence_options(main_window, config):
    """Save sequence options to the config"""
    if "Sequence Options" not in config:
        config["Sequence Options"] = {}
    
    # Save launch sequence
    if hasattr(main_window, 'launch_sequence_list'):
        launch_sequence = []
        for i in range(main_window.launch_sequence_list.count()):
            launch_sequence.append(main_window.launch_sequence_list.item(i).text())
        config["Sequence Options"]["launch_sequence"] = "|".join(launch_sequence)
        
        # Also save in Sequences section for Game.ini compatibility
        if "Sequences" not in config:
            config["Sequences"] = {}
        config["Sequences"]["default_launch_sequence"] = ",".join(launch_sequence)
    
    # Save exit sequence
    if hasattr(main_window, 'exit_sequence_list'):
        exit_sequence = []
        for i in range(main_window.exit_sequence_list.count()):
            exit_sequence.append(main_window.exit_sequence_list.item(i).text())
        config["Sequence Options"]["exit_sequence"] = "|".join(exit_sequence)
        
        # Also save in Sequences section for Game.ini compatibility
        if "Sequences" not in config:
            config["Sequences"] = {}
        config["Sequences"]["default_exit_sequence"] = ",".join(exit_sequence)

def save_configuration(main_window, config_file=None):
    """Save the current configuration to config.ini"""
    try:
        # Get the current configuration
        config = gather_current_configuration(main_window)
        
        # Save sequence options
        save_sequence_options(main_window, config)
        
        # Get the app's root directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        app_root_dir = os.path.dirname(os.path.dirname(script_dir))
        
        if config_file is None:
            config_path = os.path.join(app_root_dir, "config.ini")
        else:
            config_path = config_file
        
        # Add deployment options to Current Settings
        if hasattr(main_window, 'create_overwrite_joystick_profiles_checkbox'):
            config["Current Settings"]["deployment_create_overwrite_joystick_profiles"] = str(main_window.create_overwrite_joystick_profiles_checkbox.isChecked())
        
        # Save the configuration
        with open(config_path, 'w', encoding='utf-8') as f:
            config.write(f)
        

        return True
    except Exception as e:

        return False

def load_sequence_options(main_window, config):
    """Load sequence options from the config"""
    if "Sequence Options" in config:
        # Load launch sequence
        if hasattr(main_window, 'launch_sequence_list') and "launch_sequence" in config["Sequence Options"]:
            launch_sequence = config["Sequence Options"]["launch_sequence"].split("|")
            if launch_sequence:
                main_window.launch_sequence_list.clear()
                main_window.launch_sequence_list.addItems(launch_sequence)
        
        # Load exit sequence
        if hasattr(main_window, 'exit_sequence_list') and "exit_sequence" in config["Sequence Options"]:
            exit_sequence = config["Sequence Options"]["exit_sequence"].split("|")
            if exit_sequence:
                main_window.exit_sequence_list.clear()
                main_window.exit_sequence_list.addItems(exit_sequence)

def load_configuration(main_window, config_path=None):
    """Load the configuration from config.ini"""
    try:
        # Get the app's root directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        app_root_dir = os.path.dirname(os.path.dirname(script_dir))
        
        if config_path is None:
            config_path = os.path.join(app_root_dir, "config.ini")
        
        if not os.path.exists(config_path):

            return False
        
        config = configparser.ConfigParser()
        config.read(config_path, encoding='utf-8')
        
        # Helper function to get boolean values
        def get_bool(section, key, default=False):
            if section in config and key in config[section]:
                return config[section][key].lower() in ('true', 'yes', '1', 'on')
            return default
        
        # Helper function to set text if not empty
        def set_text_if_not_empty(widget, text):
            if text:
                widget.setText(text)
        
        # Helper function to set combo items
        def set_combo_items(combo, items_str):
            if items_str:
                combo.clear()
                items = items_str.split('|')
                combo.addItems(items)
        

        
        # --- Current Settings ---
        if "Current Settings" in config:
            cs = config["Current Settings"]
            set_combo_items(main_window.source_dirs_combo, cs.get("source_directories", ''))
            set_combo_items(main_window.exclude_items_combo, cs.get("exclude_items", ''))
            
            # Set current text for combo boxes only if the value exists
            if cs.get("game_managers_present", ''):
                main_window.other_managers_combo.setCurrentText(cs.get("game_managers_present"))
            if cs.get("logging_verbosity", ''):
                main_window.logging_verbosity_combo.setCurrentText(cs.get("logging_verbosity"))
            
            # Set checkboxes
            if hasattr(main_window, 'exclude_manager_checkbox'):
                main_window.exclude_manager_checkbox.setChecked(get_bool("Current Settings", "exclude_selected_manager_games"))
            
            # Set deployment checkboxes
            if hasattr(main_window, 'net_check_checkbox'):
                main_window.net_check_checkbox.setChecked(get_bool("Current Settings", "deployment_net_check"))
            if hasattr(main_window, 'name_check_checkbox'):
                main_window.name_check_checkbox.setChecked(get_bool("Current Settings", "deployment_name_check"))
            if hasattr(main_window, 'create_profile_folders_checkbox'):
                main_window.create_profile_folders_checkbox.setChecked(get_bool("Current Settings", "deployment_create_profile_folders"))
            if hasattr(main_window, 'use_kill_list_checkbox'):
                main_window.use_kill_list_checkbox.setChecked(get_bool("Current Settings", "deployment_use_kill_list"))
            if hasattr(main_window, 'run_as_admin_checkbox'): 
                main_window.run_as_admin_checkbox.setChecked(get_bool("Current Settings", "deployment_run_as_admin"))
            if hasattr(main_window, 'hide_taskbar_checkbox'): 
                main_window.hide_taskbar_checkbox.setChecked(get_bool("Current Settings", "deployment_hide_taskbar"))
            if hasattr(main_window, 'enable_launcher_checkbox'): 
                main_window.enable_launcher_checkbox.setChecked(get_bool("Current Settings", "deployment_enable_launcher"))
            if hasattr(main_window, 'apply_mapper_profiles_checkbox'): 
                main_window.apply_mapper_profiles_checkbox.setChecked(get_bool("Current Settings", "deployment_apply_mapper_profiles"))
            if hasattr(main_window, 'enable_borderless_windowing_checkbox'): 
                main_window.enable_borderless_windowing_checkbox.setChecked(get_bool("Current Settings", "deployment_enable_borderless_windowing"))
            if hasattr(main_window, 'terminate_bw_on_exit_checkbox'): 
                main_window.terminate_bw_on_exit_checkbox.setChecked(get_bool("Current Settings", "deployment_terminate_borderless_on_exit"))
            if hasattr(main_window, 'create_overwrite_joystick_profiles_checkbox'):
                main_window.create_overwrite_joystick_profiles_checkbox.setChecked(get_bool("Current Settings", "deployment_create_overwrite_joystick_profiles"))

        # Load CEN/LC options
        if "Deployment Options" in config and hasattr(main_window, 'deployment_path_options'):
            do = config["Deployment Options"]
            for path_key, radio_group in main_window.deployment_path_options.items():
                mode = do.get(f"{path_key}_mode", "CEN")
                for button in radio_group.buttons():
                    if button.text() == mode:
                        button.setChecked(True)
                        break

        # --- Element Locations ---
        if "Element Locations" in config:
            el = config["Element Locations"]
            if hasattr(main_window, 'profiles_dir_edit'): 
                set_text_if_not_empty(main_window.profiles_dir_edit, el.get("profiles_directory", ''))
            if hasattr(main_window, 'launchers_dir_edit'): 
                set_text_if_not_empty(main_window.launchers_dir_edit, el.get("launchers_directory", ''))
            if hasattr(main_window, 'p1_profile_edit'): 
                set_text_if_not_empty(main_window.p1_profile_edit, el.get("player_1_profile_file", ''))
            if hasattr(main_window, 'p2_profile_edit'): 
                set_text_if_not_empty(main_window.p2_profile_edit, el.get("player_2_profile_file", ''))
            if hasattr(main_window, 'mediacenter_profile_edit'): 
                set_text_if_not_empty(main_window.mediacenter_profile_edit, el.get("mediacenter_desktop_profile_file", ''))
            if hasattr(main_window, 'multimonitor_gaming_config_edit'): 
                set_text_if_not_empty(main_window.multimonitor_gaming_config_edit, el.get("multimonitor_gaming_config_file", ''))
            if hasattr(main_window, 'multimonitor_media_config_edit'): 
                set_text_if_not_empty(main_window.multimonitor_media_config_edit, el.get("multimonitor_media_desktop_config_file", ''))
            
            # Set steam paths only if they exist in the config
            if el.get("steam_json_path", ''):
                main_window.steam_json_file_path = el.get("steam_json_path", '')
            if el.get("filtered_steam_cache_path", ''):
                main_window.filtered_steam_cache_file_path = el.get("filtered_steam_cache_path", '')

        # --- App Locations ---
        if "App Locations" in config:
            al = config["App Locations"]
            if hasattr(main_window, 'controller_mapper_app_line_edit'): 
                set_text_if_not_empty(main_window.controller_mapper_app_line_edit, al.get("controller_mapper_app", ''))
            if hasattr(main_window, 'borderless_app_line_edit'): 
                set_text_if_not_empty(main_window.borderless_app_line_edit, al.get("borderless_windowing_app", ''))
            if hasattr(main_window, 'multimonitor_app_line_edit'): 
                set_text_if_not_empty(main_window.multimonitor_app_line_edit, al.get("multi_monitor_app", ''))
            
            # Set pre-launch apps
            if hasattr(main_window, 'pre_launch_app_line_edits'):
                for i, le in enumerate(main_window.pre_launch_app_line_edits):
                    set_text_if_not_empty(le, al.get(f"pre_launch_app_{i+1}", ''))
                    
            # Set post-launch apps
            if hasattr(main_window, 'post_launch_app_line_edits'):
                for i, le in enumerate(main_window.post_launch_app_line_edits):
                    set_text_if_not_empty(le, al.get(f"post_launch_app_{i+1}", ''))
            
            # Set run-wait checkboxes for pre-launch apps
            if hasattr(main_window, 'pre_launch_run_wait_checkboxes'):
                for i, cb in enumerate(main_window.pre_launch_run_wait_checkboxes):
                    cb.setChecked(get_bool("App Locations", f"pre_launch_app_{i+1}_run_wait"))
            
            # Set run-wait checkboxes for post-launch apps
            if hasattr(main_window, 'post_launch_run_wait_checkboxes'):
                for i, cb in enumerate(main_window.post_launch_run_wait_checkboxes):
                    cb.setChecked(get_bool("App Locations", f"post_launch_app_{i+1}_run_wait"))

        # --- Sequence Options ---
        load_sequence_options(main_window, config)
        
        return True
    except Exception as e:

        import traceback
        traceback.print_exc()
        return False

def show_import_configuration_dialog(main_window):
    """Show a file dialog to load configuration"""
    file_path, _ = QFileDialog.getOpenFileName(main_window, "Open Configuration File", "", "INI Files (*.ini);;All Files (*)")
    if file_path:
        load_configuration(main_window, file_path)

def connect_dynamic_config_saving(main_window):
    """Connect UI elements to save configuration dynamically when changed"""
    print("Connecting dynamic config saving")
    
    # Connect checkboxes
    checkboxes = []
    
    # Add deployment checkboxes if they exist
    if hasattr(main_window, 'net_check_checkbox') and main_window.net_check_checkbox is not None:
        checkboxes.append(main_window.net_check_checkbox)
    if hasattr(main_window, 'name_check_checkbox') and main_window.name_check_checkbox is not None:
        checkboxes.append(main_window.name_check_checkbox)
    if hasattr(main_window, 'create_profile_folders_checkbox') and main_window.create_profile_folders_checkbox is not None:
        checkboxes.append(main_window.create_profile_folders_checkbox)
    if hasattr(main_window, 'use_kill_list_checkbox') and main_window.use_kill_list_checkbox is not None:
        checkboxes.append(main_window.use_kill_list_checkbox)
    if hasattr(main_window, 'run_as_admin_checkbox') and main_window.run_as_admin_checkbox is not None:
        checkboxes.append(main_window.run_as_admin_checkbox)
    if hasattr(main_window, 'hide_taskbar_checkbox') and main_window.hide_taskbar_checkbox is not None:
        checkboxes.append(main_window.hide_taskbar_checkbox)
    if hasattr(main_window, 'enable_launcher_checkbox') and main_window.enable_launcher_checkbox is not None:
        checkboxes.append(main_window.enable_launcher_checkbox)
    if hasattr(main_window, 'apply_mapper_profiles_checkbox') and main_window.apply_mapper_profiles_checkbox is not None:
        checkboxes.append(main_window.apply_mapper_profiles_checkbox)
    if hasattr(main_window, 'enable_borderless_windowing_checkbox') and main_window.enable_borderless_windowing_checkbox is not None:
        checkboxes.append(main_window.enable_borderless_windowing_checkbox)
    if hasattr(main_window, 'terminate_bw_on_exit_checkbox') and main_window.terminate_bw_on_exit_checkbox is not None:
        checkboxes.append(main_window.terminate_bw_on_exit_checkbox)
    if hasattr(main_window, 'exclude_manager_checkbox') and main_window.exclude_manager_checkbox is not None:
        checkboxes.append(main_window.exclude_manager_checkbox)
    if hasattr(main_window, 'create_overwrite_joystick_profiles_checkbox') and main_window.create_overwrite_joystick_profiles_checkbox is not None:
        checkboxes.append(main_window.create_overwrite_joystick_profiles_checkbox)
    
    # Add run wait checkboxes if they exist
    if hasattr(main_window, 'after_launch_run_wait_checkbox') and main_window.after_launch_run_wait_checkbox is not None:
        checkboxes.append(main_window.after_launch_run_wait_checkbox)
    if hasattr(main_window, 'before_exit_run_wait_checkbox') and main_window.before_exit_run_wait_checkbox is not None:
        checkboxes.append(main_window.before_exit_run_wait_checkbox)
    if hasattr(main_window, 'pre_launch_run_wait_checkboxes'):
        for cb in main_window.pre_launch_run_wait_checkboxes:
            if cb is not None:
                checkboxes.append(cb)
    if hasattr(main_window, 'post_launch_run_wait_checkboxes'):
        for cb in main_window.post_launch_run_wait_checkboxes:
            if cb is not None:
                checkboxes.append(cb)
    
    for checkbox in checkboxes:
        try:
            checkbox.toggled.connect(lambda checked, mw=main_window: save_configuration(mw))
        except RuntimeError as e:
            pass
    
    # Connect radio buttons for CEN/LC options
    if hasattr(main_window, 'deployment_path_options'):
        for path_key, radio_group in main_window.deployment_path_options.items():
            try:
                # Check if the radio group is valid
                if radio_group is not None and hasattr(radio_group, 'buttons'):
                    for button in radio_group.buttons():
                        if button is not None:
                            button.toggled.connect(lambda checked, mw=main_window: save_configuration(mw))
            except RuntimeError as e:

                continue
    
    # Connect line edits
    line_edits = []
    
    # Add setup tab line edits
    if hasattr(main_window, 'profiles_dir_edit') and main_window.profiles_dir_edit is not None:
        line_edits.append(main_window.profiles_dir_edit)
    if hasattr(main_window, 'launchers_dir_edit') and main_window.launchers_dir_edit is not None:
        line_edits.append(main_window.launchers_dir_edit)
    if hasattr(main_window, 'controller_mapper_app_line_edit') and main_window.controller_mapper_app_line_edit is not None:
        line_edits.append(main_window.controller_mapper_app_line_edit)
    if hasattr(main_window, 'borderless_app_line_edit') and main_window.borderless_app_line_edit is not None:
        line_edits.append(main_window.borderless_app_line_edit)
    if hasattr(main_window, 'multimonitor_app_line_edit') and main_window.multimonitor_app_line_edit is not None:
        line_edits.append(main_window.multimonitor_app_line_edit)
    if hasattr(main_window, 'p1_profile_edit') and main_window.p1_profile_edit is not None:
        line_edits.append(main_window.p1_profile_edit)
    if hasattr(main_window, 'p2_profile_edit') and main_window.p2_profile_edit is not None:
        line_edits.append(main_window.p2_profile_edit)
    if hasattr(main_window, 'mediacenter_profile_edit') and main_window.mediacenter_profile_edit is not None:
        line_edits.append(main_window.mediacenter_profile_edit)
    if hasattr(main_window, 'multimonitor_gaming_config_edit') and main_window.multimonitor_gaming_config_edit is not None:
        line_edits.append(main_window.multimonitor_gaming_config_edit)
    if hasattr(main_window, 'multimonitor_media_config_edit') and main_window.multimonitor_media_config_edit is not None:
        line_edits.append(main_window.multimonitor_media_config_edit)
    
    # Add pre-launch and post-launch app line edits
    if hasattr(main_window, 'pre_launch_app_line_edits'):
        for le in main_window.pre_launch_app_line_edits:
            if le is not None:
                line_edits.append(le)
    if hasattr(main_window, 'post_launch_app_line_edits'):
        for le in main_window.post_launch_app_line_edits:
            if le is not None:
                line_edits.append(le)
    
    for line_edit in line_edits:
        try:
            line_edit.textChanged.connect(lambda text, mw=main_window: save_configuration(mw))
        except RuntimeError as e:
            pass
    
    # Connect combo boxes
    combo_boxes = []
    
    if hasattr(main_window, 'source_dirs_combo') and main_window.source_dirs_combo is not None:
        combo_boxes.append(main_window.source_dirs_combo)
    if hasattr(main_window, 'exclude_items_combo') and main_window.exclude_items_combo is not None:
        combo_boxes.append(main_window.exclude_items_combo)
    if hasattr(main_window, 'other_managers_combo') and main_window.other_managers_combo is not None:
        combo_boxes.append(main_window.other_managers_combo)
    if hasattr(main_window, 'logging_verbosity_combo') and main_window.logging_verbosity_combo is not None:
        combo_boxes.append(main_window.logging_verbosity_combo)
    
    for combo_box in combo_boxes:
        try:
            combo_box.currentTextChanged.connect(lambda text, mw=main_window: save_configuration(mw))
        except RuntimeError as e:
            pass
    
    # Connect sequence lists
    if hasattr(main_window, 'launch_sequence_list') and main_window.launch_sequence_list is not None:
        try:
            # Connect to model's dataChanged signal
            main_window.launch_sequence_list.model().dataChanged.connect(
                lambda topLeft, bottomRight, roles, mw=main_window: save_configuration(mw))
            # Connect to model's rowsMoved signal
            main_window.launch_sequence_list.model().rowsMoved.connect(
                lambda parent, start, end, destination, row, mw=main_window: save_configuration(mw))
        except (RuntimeError, AttributeError) as e:
            pass
    
    if hasattr(main_window, 'exit_sequence_list') and main_window.exit_sequence_list is not None:
        try:
            # Connect to model's dataChanged signal
            main_window.exit_sequence_list.model().dataChanged.connect(
                lambda topLeft, bottomRight, roles, mw=main_window: save_configuration(mw))
            # Connect to model's rowsMoved signal
            main_window.exit_sequence_list.model().rowsMoved.connect(
                lambda parent, start, end, destination, row, mw=main_window: save_configuration(mw))
        except (RuntimeError, AttributeError) as e:
            pass
    
    print("Dynamic config saving connected successfully")

def load_initial_config(main_window):
    """Load the initial configuration when the application starts"""
    try:
        # Get the app's root directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        app_root_dir = os.path.dirname(os.path.dirname(script_dir))
        
        # Define the config file path
        config_file = os.path.join(app_root_dir, 'config.ini')
        
        # Load the configuration
        load_configuration(main_window, config_file)
        
        # Add a debug print to confirm this function is being called
        print(f"Initial configuration loaded from {config_file}")
        
    except Exception as e:
        print(f"Error loading initial configuration: {str(e)}")

def load_default_config(main_window):
    """Load default configuration from config.set template"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_root_dir = os.path.dirname(os.path.dirname(script_dir))
    config_set_path = os.path.join(app_root_dir, "Python", "config.set")
    
    if not os.path.exists(config_set_path):

        return False
    
    try:
        # Load the default config
        default_config = configparser.ConfigParser()
        default_config.read(config_set_path, encoding='utf-8')
        
        # Set app_directory
        if "Current Settings" in default_config:
            default_config["Current Settings"]["app_directory"] = app_root_dir
        
        # Apply the default configuration
        apply_loaded_configuration(main_window, default_config)
        
        # Save the configuration to create a new config.ini
        config_file = os.path.join(app_root_dir, "config.ini")
        save_configuration(main_window, config_file)
        

        return True
    except Exception as e:

        import traceback
        traceback.print_exc()
        return False

def initialize_repos_config(config_file=None):
    """Initialize repos.ini based on Python\repos.set and app_directory from config.ini"""
    # Get the app's root directory if config_file is not specified
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_root_dir = os.path.dirname(os.path.dirname(script_dir))
    
    if config_file is None:
        config_file = os.path.join(app_root_dir, "config.ini")
    
    # Load the main config to get app_directory
    main_config = configparser.ConfigParser()
    main_config.read(config_file, encoding='utf-8')
    
    app_directory = main_config.get("Current Settings", "app_directory", fallback=app_root_dir)
    
    # Load repos.set
    repos_set_path = os.path.join(app_directory, "repos.set")
    if not os.path.exists(repos_set_path):
        # Try the Python subdirectory
        repos_set_path = os.path.join(app_directory, "Python", "repos.set")
        if not os.path.exists(repos_set_path):
            print(f"repos.set not found at {repos_set_path}")
            return False
    
    # Read repos.set content
    with open(repos_set_path, 'r', encoding='utf-8') as f:
        repos_set_content = f.read()
    
    # Parse GLOBAL section
    global_section = ""
    in_global_section = False
    for line in repos_set_content.splitlines():
        if line.strip() == "[GLOBAL]":
            in_global_section = True
            continue
        elif line.strip().startswith("[") and line.strip().endswith("]"):
            in_global_section = False
        
        if in_global_section:
            global_section += line + "\n"
    
    # Create repos.ini
    repos_ini_path = os.path.join(app_directory, "repos.ini")
    
    # Check if repos.ini already exists and has content
    if os.path.exists(repos_ini_path):
        with open(repos_ini_path, 'r', encoding='utf-8') as f:
            existing_content = f.read().strip()
        
        # If it has content, don't overwrite it
        if existing_content:
            print(f"repos.ini already exists with content, not overwriting")
            return True
    
    # Write to repos.ini
    with open(repos_ini_path, 'w', encoding='utf-8') as f:
        f.write("[Current Settings]\n")
        f.write(global_section)
    
    print(f"Created repos.ini at {repos_ini_path}")
    return True

def validate_and_repair_config(main_window):
    """Validate the config.ini file and repair it if necessary"""
    # Get the app's root directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_root_dir = os.path.dirname(os.path.dirname(script_dir))
    config_file = os.path.join(app_root_dir, "config.ini")
    
    # Check if config.ini exists
    if not os.path.exists(config_file):

        # Create a new config file
        save_configuration(main_window, config_file)
        return
    
    # Load the config file
    config = configparser.ConfigParser()
    config.optionxform = str  # Preserve case for keys
    
    try:
        config.read(config_file, encoding='utf-8')
    except Exception as e:

        # Backup the corrupted file
        backup_file = f"{config_file}.bak"
        try:
            import shutil
            shutil.copy2(config_file, backup_file)

        except Exception as e:
            pass
        
        # Create a new config file
        save_configuration(main_window, config_file)
        return
    
    # Check if required sections exist
    required_sections = ["Current Settings", "Element Locations", "App Locations", "Deployment Options"]
    missing_sections = [section for section in required_sections if section not in config]

    # If any required sections are missing, repair the config file
    if missing_sections:

        # Create a new config file
        save_configuration(main_window, config_file)
        return
    
    # Check if required keys exist in Current Settings
    required_keys = {
        "Current Settings": ["app_directory", "source_directories", "exclude_items", 
                            "game_managers_present", "exclude_selected_manager_games", 
                            "logging_verbosity"],
        "Element Locations": ["profiles_directory", "launchers_directory"],
        "App Locations": []
    }
    
    for section, keys in required_keys.items():
        if section in config:
            missing_keys = [key for key in keys if key not in config[section]]
            if missing_keys:

                # Update the config file
                save_configuration(main_window, config_file)
                return
    
    # Check if any values are None or empty when they shouldn't be
    critical_keys = {
        "Current Settings": ["app_directory"],
        "Element Locations": ["profiles_directory", "launchers_directory"]
    }
    
    for section, keys in critical_keys.items():
        if section in config:
            for key in keys:
                if key in config[section] and not config[section][key]:

                    # Update the config file
                    save_configuration(main_window, config_file)
                    return

def save_launch_exit_sequences(main_window, launch_sequence, exit_sequence):
    """Save the launch and exit sequences to config.ini"""
    try:
        # Get the current configuration
        config = gather_current_configuration(main_window)
        
        # Ensure the Sequences section exists
        if "Sequences" not in config:
            config["Sequences"] = {}
        
        # Save the sequences
        if launch_sequence:
            config["Sequences"]["default_launch_sequence"] = ','.join(launch_sequence)
        
        if exit_sequence:
            config["Sequences"]["default_exit_sequence"] = ','.join(exit_sequence)
        
        # Get the app's root directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        app_root_dir = os.path.dirname(os.path.dirname(script_dir))
        config_path = os.path.join(app_root_dir, "config.ini")
        
        # Save the configuration
        with open(config_path, 'w', encoding='utf-8') as f:
            config.write(f)
        

        return True
    except Exception as e:

        return False

def get_launch_exit_sequences(main_window):
    """Get the launch and exit sequences from config.ini"""
    try:
        # Get the app's root directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        app_root_dir = os.path.dirname(os.path.dirname(script_dir))
        config_path = os.path.join(app_root_dir, "config.ini")
        
        if not os.path.exists(config_path):

            return None, None
        
        config = configparser.ConfigParser()
        config.read(config_path, encoding='utf-8')
        
        launch_sequence = None
        exit_sequence = None
        
        if "Sequences" in config:
            # Get launch sequence
            if "default_launch_sequence" in config["Sequences"]:
                launch_sequence_str = config["Sequences"]["default_launch_sequence"]
                if launch_sequence_str:
                    launch_sequence = launch_sequence_str.split(',')
            
            # Get exit sequence
            if "default_exit_sequence" in config["Sequences"]:
                exit_sequence_str = config["Sequences"]["default_exit_sequence"]
                if exit_sequence_str:
                    exit_sequence = exit_sequence_str.split(',')
        
        return launch_sequence, exit_sequence
    except Exception as e:

        return None, None

def apply_loaded_configuration(main_window, config):
    """Apply the loaded configuration to the UI elements"""
    try:
        # Helper function to get boolean values
        def get_bool(section, key, default=False):
            if section in config and key in config[section]:
                return config[section][key].lower() in ('true', 'yes', '1', 'on')
            return default
        
        # Helper function to set text if not empty
        def set_text_if_not_empty(widget, text):
            if text:
                widget.setText(text)
        
        # Helper function to set combo items
        def set_combo_items(combo, items_str):
            if items_str:
                combo.clear()
                items = items_str.split('|')
                combo.addItems(items)
        
        # --- Current Settings ---
        if "Current Settings" in config:
            cs = config["Current Settings"]
            set_combo_items(main_window.source_dirs_combo, cs.get("source_directories", ''))
            set_combo_items(main_window.exclude_items_combo, cs.get("exclude_items", ''))
            
            # Set current text for combo boxes only if the value exists
            if cs.get("game_managers_present", ''):
                main_window.other_managers_combo.setCurrentText(cs.get("game_managers_present"))
            if cs.get("logging_verbosity", ''):
                main_window.logging_verbosity_combo.setCurrentText(cs.get("logging_verbosity"))
            
            # Set checkboxes
            if hasattr(main_window, 'exclude_manager_checkbox'):
                main_window.exclude_manager_checkbox.setChecked(get_bool("Current Settings", "exclude_selected_manager_games"))
            
            # Set deployment checkboxes
            if hasattr(main_window, 'net_check_checkbox'):
                main_window.net_check_checkbox.setChecked(get_bool("Current Settings", "deployment_net_check"))
            if hasattr(main_window, 'name_check_checkbox'):
                main_window.name_check_checkbox.setChecked(get_bool("Current Settings", "deployment_name_check"))
            if hasattr(main_window, 'create_profile_folders_checkbox'):
                main_window.create_profile_folders_checkbox.setChecked(get_bool("Current Settings", "deployment_create_profile_folders"))
            if hasattr(main_window, 'use_kill_list_checkbox'):
                main_window.use_kill_list_checkbox.setChecked(get_bool("Current Settings", "deployment_use_kill_list"))
            if hasattr(main_window, 'run_as_admin_checkbox'): 
                main_window.run_as_admin_checkbox.setChecked(get_bool("Current Settings", "deployment_run_as_admin"))
            if hasattr(main_window, 'hide_taskbar_checkbox'): 
                main_window.hide_taskbar_checkbox.setChecked(get_bool("Current Settings", "deployment_hide_taskbar"))
            if hasattr(main_window, 'enable_launcher_checkbox'): 
                main_window.enable_launcher_checkbox.setChecked(get_bool("Current Settings", "deployment_enable_launcher"))
            if hasattr(main_window, 'apply_mapper_profiles_checkbox'): 
                main_window.apply_mapper_profiles_checkbox.setChecked(get_bool("Current Settings", "deployment_apply_mapper_profiles"))
            if hasattr(main_window, 'enable_borderless_windowing_checkbox'): 
                main_window.enable_borderless_windowing_checkbox.setChecked(get_bool("Current Settings", "deployment_enable_borderless_windowing"))
            if hasattr(main_window, 'terminate_bw_on_exit_checkbox'): 
                main_window.terminate_bw_on_exit_checkbox.setChecked(get_bool("Current Settings", "deployment_terminate_borderless_on_exit"))
            if hasattr(main_window, 'create_overwrite_joystick_profiles_checkbox'):
                main_window.create_overwrite_joystick_profiles_checkbox.setChecked(get_bool("Current Settings", "deployment_create_overwrite_joystick_profiles"))

        # --- Element Locations ---
        if "Element Locations" in config:
            el = config["Element Locations"]
            if hasattr(main_window, 'profiles_dir_edit'): 
                set_text_if_not_empty(main_window.profiles_dir_edit, el.get("profiles_directory", ''))
            if hasattr(main_window, 'launchers_dir_edit'): 
                set_text_if_not_empty(main_window.launchers_dir_edit, el.get("launchers_directory", ''))
            if hasattr(main_window, 'p1_profile_edit'): 
                set_text_if_not_empty(main_window.p1_profile_edit, el.get("player_1_profile_file", ''))
            if hasattr(main_window, 'p2_profile_edit'): 
                set_text_if_not_empty(main_window.p2_profile_edit, el.get("player_2_profile_file", ''))
            if hasattr(main_window, 'mediacenter_profile_edit'): 
                set_text_if_not_empty(main_window.mediacenter_profile_edit, el.get("mediacenter_desktop_profile_file", ''))
            if hasattr(main_window, 'multimonitor_gaming_config_edit'): 
                set_text_if_not_empty(main_window.multimonitor_gaming_config_edit, el.get("multimonitor_gaming_config_file", ''))
            if hasattr(main_window, 'multimonitor_media_config_edit'): 
                set_text_if_not_empty(main_window.multimonitor_media_config_edit, el.get("multimonitor_media_desktop_config_file", ''))
            
            # Set steam paths only if they exist in the config
            if el.get("steam_json_path", ''):
                main_window.steam_json_file_path = el.get("steam_json_path", '')
            if el.get("filtered_steam_cache_path", ''):
                main_window.filtered_steam_cache_file_path = el.get("filtered_steam_cache_path", '')

        # --- App Locations ---
        if "App Locations" in config:
            al = config["App Locations"]
            if hasattr(main_window, 'controller_mapper_app_line_edit'): 
                set_text_if_not_empty(main_window.controller_mapper_app_line_edit, al.get("controller_mapper_app", ''))
            if hasattr(main_window, 'borderless_app_line_edit'): 
                set_text_if_not_empty(main_window.borderless_app_line_edit, al.get("borderless_windowing_app", ''))
            if hasattr(main_window, 'multimonitor_app_line_edit'): 
                set_text_if_not_empty(main_window.multimonitor_app_line_edit, al.get("multi_monitor_app", ''))
            
            # Set pre-launch apps
            if hasattr(main_window, 'pre_launch_app_line_edits'):
                for i, le in enumerate(main_window.pre_launch_app_line_edits):
                    set_text_if_not_empty(le, al.get(f"pre_launch_app_{i+1}", ''))
                    
            # Set post-launch apps
            if hasattr(main_window, 'post_launch_app_line_edits'):
                for i, le in enumerate(main_window.post_launch_app_line_edits):
                    set_text_if_not_empty(le, al.get(f"post_launch_app_{i+1}", ''))
            
            # Set run-wait checkboxes for pre-launch apps
            if hasattr(main_window, 'pre_launch_run_wait_checkboxes'):
                for i, cb in enumerate(main_window.pre_launch_run_wait_checkboxes):
                    cb.setChecked(get_bool("App Locations", f"pre_launch_app_{i+1}_run_wait"))
            
            # Set run-wait checkboxes for post-launch apps
            if hasattr(main_window, 'post_launch_run_wait_checkboxes'):
                for i, cb in enumerate(main_window.post_launch_run_wait_checkboxes):
                    cb.setChecked(get_bool("App Locations", f"post_launch_app_{i+1}_run_wait"))

        # --- Sequence Options ---
        load_sequence_options(main_window, config)
        
        return True
    except Exception as e:

        import traceback
        traceback.print_exc()
        return False
