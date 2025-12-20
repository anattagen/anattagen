import os
import json
import time
import re
from PyQt6.QtCore import Qt, QCoreApplication
from PyQt6.QtWidgets import (
    QProgressDialog, QTableWidgetItem, QCheckBox, QComboBox, QPushButton, 
    QLabel, QWidget, QHBoxLayout, QMessageBox
)
from Python.ui.name_processor import NameProcessor
from Python.ui.name_utils import normalize_name_for_matching, make_safe_filename, to_snake_case
from Python.ui.steam_utils import locate_and_exclude_manager_config
from Python import constants

def index_games(main_window, enable_name_matching=False):
    """
    Index games from the source directories
    
    Args:
        main_window: The main application window
        enable_name_matching: Whether to enable name matching with Steam
    
    Returns:
        Number of executables found
    """
    # Reset the indexing cancelled flag
    main_window.indexing_cancelled = False
    
    # Create a progress dialog
    main_window.indexing_progress = QProgressDialog("Indexing games...", "Cancel", 0, 100, main_window)
    main_window.indexing_progress.setWindowTitle("Indexing Games")
    main_window.indexing_progress.setWindowModality(Qt.WindowModality.WindowModal)
    main_window.indexing_progress.setMinimumDuration(0)
    main_window.indexing_progress.setValue(0)
    main_window.indexing_progress.canceled.connect(lambda: setattr(main_window, 'indexing_cancelled', True))
    main_window.indexing_progress.show()
    
    # Perform indexing
    result = _perform_indexing_with_updates(main_window, enable_name_matching)
    
    # Clean up
    if hasattr(main_window, 'indexing_progress'):
        main_window.indexing_progress.close()
        main_window.indexing_progress = None
    
    return result

def _perform_indexing_with_updates(main_window, enable_name_matching=False):
    """
    Perform the actual indexing with UI updates
    
    Args:
        main_window: The main application window
        enable_name_matching: Whether to enable name matching with Steam
    
    Returns:
        Number of executables found
    """
    # If requested, exclude games from selected manager
    selected_manager = main_window.other_managers_combo.currentText()
    if selected_manager != "(None)" and main_window.exclude_manager_checkbox.isChecked():
        main_window._locate_and_exclude_manager_config()
    
    # Clear the existing table
    main_window.editor_table.setRowCount(0)
    main_window.found_executables_cache = set()  # Reset cache
    
    # Process each source directory
    source_count = 0
    for i in range(main_window.source_dirs_combo.count()):
        if main_window.indexing_cancelled:
            break
        
        source_dir = main_window.source_dirs_combo.itemText(i)
        if os.path.exists(source_dir):
            source_count += traverse_source_directory(main_window, source_dir, source_dir, enable_name_matching)
    
    # Update status bar
    main_window.statusBar().showMessage(f"Indexed {source_count} executables", 3000)
    
    return source_count

def _confirm_cancel_indexing(main_window):
    """Show confirmation dialog for cancelling indexing"""
    from PyQt6.QtWidgets import QMessageBox
    reply = QMessageBox.question(
        main_window, 
        'Cancel Indexing',
        'Are you sure you want to cancel the indexing process?',
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No
    )
    if reply == QMessageBox.StandardButton.Yes:
        main_window.indexing_cancelled = True
        main_window.statusBar().showMessage("Indexing cancelled by user")

def _finish_indexing(main_window):
    """Clean up after indexing is complete or cancelled"""
    main_window.indexing_in_progress = False
    main_window.editor_table.setEnabled(True)
    
    # Hide cancel button
    if hasattr(main_window, 'cancel_indexing_button'):
        main_window.cancel_indexing_button.hide()
        # If it was added to status bar, remove it
        main_window.statusBar().removeWidget(main_window.cancel_indexing_button)

def get_filtered_directory_name(main_window, exec_full_path):
    """
    Walk up the directory tree from the executable path and find the first directory
    that is not in the folder_exclude set.
    
    Args:
        main_window: The main application window
        exec_full_path: The full path to the executable
        
    Returns:
        The name of the first non-excluded directory
    """
    # Get the directory path
    dir_path = os.path.dirname(exec_full_path)
    
    # Check if folder_exclude_set exists
    if not hasattr(main_window, 'folder_exclude_set') or not main_window.folder_exclude_set:
        # If no exclusion set, just return the immediate directory name
        return os.path.basename(dir_path)
    
    # Walk up the directory tree
    current_path = dir_path
    while True:
        # Get the current directory name
        dir_name = os.path.basename(current_path)
        
        # Check if this directory name is in the exclude set
        if dir_name.lower() not in main_window.folder_exclude_set:
            return dir_name
        
        pass
        
        # Go up one level
        parent_path = os.path.dirname(current_path)
        
        # If we've reached the root or haven't changed directories, stop
        if parent_path == current_path:
            # If all directories are excluded, return the original directory name
            pass
            return os.path.basename(dir_path)
        
        current_path = parent_path

def traverse_source_directory(main_window, current_dir_path, source_root_path, enable_name_matching=False):
    """
    Traverse a source directory looking for executables
    
    Args:
        main_window: The main application window
        current_dir_path: The current directory path
        source_root_path: The source root path
        enable_name_matching: Whether to enable name matching with Steam
    
    Returns:
        Number of executables added
    """
    # Initialize counter for executables added
    added_exe_count = 0
    
    # Check if indexing was cancelled
    if hasattr(main_window, 'indexing_cancelled') and main_window.indexing_cancelled:
        return 0
    
    # Process UI events periodically
    QCoreApplication.processEvents()
    
    # Create a name processor
    name_processor = NameProcessor(
        release_groups_set=main_window.release_groups_set,
        exclude_exe_set=main_window.exclude_exe_set
    )
    
    # Process the directory
    try:
        # Update progress dialog message if available
        if hasattr(main_window, 'indexing_progress') and main_window.indexing_progress:
            main_window.indexing_progress.setLabelText(f"Scanning: {current_dir_path}")
            QCoreApplication.processEvents()
        
        # Scan directory for executables
        with os.scandir(current_dir_path) as entries:
            for entry in entries:
                # Check if indexing was cancelled
                if hasattr(main_window, 'indexing_cancelled') and main_window.indexing_cancelled:
                    return added_exe_count
                
                # Get the entry path
                entry_path = entry.path
                
                # Process subdirectories recursively
                if entry.is_dir():
                    # Recursively process all subdirectories without filtering
                    added_exe_count += traverse_source_directory(main_window, entry_path, source_root_path, enable_name_matching)
                
                # Process executable files
                elif entry.is_file() and entry.name.lower().endswith('.exe'):
                    try:
                        # Get the executable name and path
                        exec_name = entry.name
                        exec_name_no_ext = os.path.splitext(exec_name)[0]  # Name without .exe extension
                        exec_full_path = entry_path
                        exec_full_path_lower = exec_full_path.lower()
                        
                        # Skip if we've already processed this executable
                        if hasattr(main_window, 'found_executables_cache') and exec_full_path_lower in main_window.found_executables_cache:
                            continue
                        
                        # Remove all non-alphanumeric characters from executable name for filtering
                        clean_exec_name = re.sub(r'[^a-zA-Z0-9]', '', exec_name_no_ext).lower()
                        
                        # Skip if this cleaned executable name is in the exclude set
                        if clean_exec_name in main_window.exclude_exe_set:
                            continue
                        
                        # Get the directory path
                        dir_path = os.path.dirname(exec_full_path)
                        
                        # Get filtered directory name for display name processing
                        dir_name = get_filtered_directory_name(main_window, exec_full_path)
                        
                        # Process the name to get a clean display name
                        name_override = name_processor.get_display_name(dir_name)
                        
                        # Determine if this executable should be included by default
                        include_by_default = True
                        
                        # Check if the executable name is in the demoted set
                        if hasattr(main_window, 'demoted_set') and main_window.demoted_set:
                            # Get the executable name without extension
                            exec_name_no_ext = os.path.splitext(exec_name)[0]  # Name without .exe extension
                            
                            # Normalize the executable name for comparison
                            normalized_exec_name = normalize_name_for_matching(exec_name_no_ext).replace(' ', '').lower()
                            
                            # Normalize the name override for comparison
                            normalized_name_override = normalize_name_for_matching(name_override).replace(' ', '').lower()
                            
                            # Process the directory name to remove tags and revisions
                            processed_dir_name = name_processor.get_display_name(dir_name)
                            normalized_dir_name = normalize_name_for_matching(processed_dir_name).replace(' ', '').lower()
                            
                            # Check if normalized executable name has any term from the demoted set at the beginning or end
                            for demoted_term in main_window.demoted_set:
                                # Check if the demoted term is at the beginning or end of the executable name AND not in the name override
                                if (normalized_exec_name.startswith(demoted_term) or normalized_exec_name.endswith(demoted_term)) and demoted_term not in normalized_name_override:
                                    include_by_default = False
                                    break
                            
                            # If not already demoted by executable name, check directory name
                            if include_by_default and hasattr(main_window, 'folder_demoted_set') and main_window.folder_demoted_set:
                                for demoted_term in main_window.folder_demoted_set:
                                    # Check if the normalized directory name EQUALS the demoted term AND that term is not in the name override
                                    if normalized_dir_name == demoted_term and demoted_term not in normalized_name_override:
                                        include_by_default = False
                                        break
                        
                        # Try to match with Steam if name matching is enabled
                        steam_name = ""
                        steam_id = ""

                        if enable_name_matching and hasattr(main_window, 'normalized_steam_match_index') and main_window.normalized_steam_match_index:
                            # Get the match name using the name processor - use the cleaned name_override
                            match_name = normalize_name_for_matching(name_override).replace(' ', '')
                            
                            # Check if we have a match in the normalized index
                            if match_name and match_name in main_window.normalized_steam_match_index:
                                match_data = main_window.normalized_steam_match_index[match_name]
                                steam_name = match_data["name"]
                                steam_id = match_data["id"]
                                
                                # Use the Steam name as the name override if it's different, but clean it first
                                if steam_name and steam_name != name_override:
                                    # Clean the Steam name to make it Windows-safe
                                    from Python.ui.name_utils import replace_illegal_chars
                                    
                                    # Replace illegal Windows characters with " - "
                                    clean_steam_name = replace_illegal_chars(steam_name, " - ")
                                    
                                    # Fix spacing issues
                                    while "  " in clean_steam_name:
                                        clean_steam_name = clean_steam_name.replace("  ", " ")
                                    
                                    # Fix double dashes
                                    while "- -" in clean_steam_name:
                                        clean_steam_name = clean_steam_name.replace("- -", " - ")
                                    
                                    # Trim leading/trailing spaces
                                    clean_steam_name = clean_steam_name.strip()
                                    
                                    # Use the cleaned Steam name as the name override
                                    name_override = clean_steam_name
                        
                        # Add to the found executables cache
                        main_window.found_executables_cache.add(exec_full_path_lower)
                        
                        # Call add_executable_to_editor_table to populate the row with defaults
                        # This function will now retrieve all default enabled states from config.defaults
                        add_executable_to_editor_table(
                            main_window,
                            include_checked=include_by_default,
                            exec_name=exec_name,
                            directory=dir_path,
                            steam_name=steam_name,
                            name_override=name_override,
                            steam_id=steam_id
                        )

                        # Update counter
                        added_exe_count += 1
                        
                        # Process UI events after each executable
                        QCoreApplication.processEvents()
                        
                    except PermissionError:
                        continue
                    except Exception as e:
                        continue
    
    except PermissionError:
        pass
    except Exception as e:
        pass
    
    return added_exe_count

def load_set_file(filename):
    """Load a .set file into a set of strings"""
    result = set()
    
    # Get the app's root directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_root_dir = os.path.dirname(os.path.dirname(script_dir))
    
    # Try app root first
    app_root_path = os.path.join(app_root_dir, filename)
    
    try:
        if os.path.exists(app_root_path):
            with open(app_root_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        result.add(line)

        elif os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        result.add(line)

        else:
            pass
    except Exception as e:
        pass
    
    return result

def add_executable_to_editor_table(main_window, include_checked=True, exec_name="", directory="", 
                                  steam_name="", name_override="", options="", arguments="", 
                                  steam_id="", as_admin=False, no_tb=False, update_ui=True):
    """
    Add an executable to the editor table, applying global default enabled states.
    """
    # Debug output



    
    # Get current row count
    row = main_window.editor_table.rowCount()
    main_window.editor_table.insertRow(row)
    
    # Create include checkbox
    include_widget = create_status_widget(main_window, include_checked, row, constants.EditorCols.INCLUDE.value)
    main_window.editor_table.setCellWidget(row, constants.EditorCols.INCLUDE.value, include_widget)

    # Retrieve global default enabled states from AppConfig
    config_defaults = main_window.config.defaults
    as_admin = main_window.config.run_as_admin # From Deployment tab
    no_tb = main_window.config.hide_taskbar # From Deployment tab
    
    # Set text items
    main_window.editor_table.setItem(row, constants.EditorCols.NAME.value, QTableWidgetItem(exec_name))
    main_window.editor_table.setItem(row, constants.EditorCols.DIRECTORY.value, QTableWidgetItem(directory))
    main_window.editor_table.setItem(row, constants.EditorCols.STEAMID.value, QTableWidgetItem(steam_name))
    main_window.editor_table.setItem(row, constants.EditorCols.NAME_OVERRIDE.value, QTableWidgetItem(name_override))
    main_window.editor_table.setItem(row, constants.EditorCols.OPTIONS.value, QTableWidgetItem(options))
    main_window.editor_table.setItem(row, constants.EditorCols.ARGUMENTS.value, QTableWidgetItem(arguments))
    # steam_id field placed in STEAMID column; additional IDs stored in name/override as needed
    
    # Populate path text fields from current setup config so they are editable in the table
    # Controller Mapper path
    main_window.editor_table.setItem(row, constants.EditorCols.CM_PATH.value, QTableWidgetItem(getattr(main_window.config, 'controller_mapper_path', '')))
    # Borderless Windowing path
    main_window.editor_table.setItem(row, constants.EditorCols.BW_PATH.value, QTableWidgetItem(getattr(main_window.config, 'borderless_gaming_path', '')))
    # Multi-monitor App path
    main_window.editor_table.setItem(row, constants.EditorCols.MM_PATH.value, QTableWidgetItem(getattr(main_window.config, 'multi_monitor_tool_path', '')))

    # Profile and MM config paths
    main_window.editor_table.setItem(row, constants.EditorCols.MM_GAME_PROFILE.value, QTableWidgetItem(getattr(main_window.config, 'multimonitor_gaming_path', '')))
    main_window.editor_table.setItem(row, constants.EditorCols.MM_DESKTOP_PROFILE.value, QTableWidgetItem(getattr(main_window.config, 'multimonitor_media_path', '')))
    main_window.editor_table.setItem(row, constants.EditorCols.PLAYER1_PROFILE.value, QTableWidgetItem(getattr(main_window.config, 'p1_profile_path', '')))
    main_window.editor_table.setItem(row, constants.EditorCols.PLAYER2_PROFILE.value, QTableWidgetItem(getattr(main_window.config, 'p2_profile_path', '')))
    main_window.editor_table.setItem(row, constants.EditorCols.MEDIACENTER_PROFILE.value, QTableWidgetItem(getattr(main_window.config, 'mediacenter_profile_path', '')))

    # Just After/Before paths
    main_window.editor_table.setItem(row, constants.EditorCols.JA_PATH.value, QTableWidgetItem(getattr(main_window.config, 'just_after_launch_path', '')))
    main_window.editor_table.setItem(row, constants.EditorCols.JB_PATH.value, QTableWidgetItem(getattr(main_window.config, 'just_before_exit_path', '')))

    # Pre/Post default paths
    main_window.editor_table.setItem(row, constants.EditorCols.PRE1_PATH.value, QTableWidgetItem(getattr(main_window.config, 'pre1_path', '')))
    main_window.editor_table.setItem(row, constants.EditorCols.POST1_PATH.value, QTableWidgetItem(getattr(main_window.config, 'post1_path', '')))
    main_window.editor_table.setItem(row, constants.EditorCols.PRE2_PATH.value, QTableWidgetItem(getattr(main_window.config, 'pre2_path', '')))
    main_window.editor_table.setItem(row, constants.EditorCols.POST2_PATH.value, QTableWidgetItem(getattr(main_window.config, 'post2_path', '')))
    main_window.editor_table.setItem(row, constants.EditorCols.PRE3_PATH.value, QTableWidgetItem(getattr(main_window.config, 'pre3_path', '')))
    main_window.editor_table.setItem(row, constants.EditorCols.POST3_PATH.value, QTableWidgetItem(getattr(main_window.config, 'post3_path', '')))
    
    # Retrieve default enabled states and run_wait states for specific features from config.defaults
    controller_mapper_enabled = config_defaults.get('controller_mapper_enabled', True)
    controller_mapper_run_wait = config_defaults.get('controller_mapper_run_wait', False)
    borderless_windowing_enabled = config_defaults.get('borderless_windowing_enabled', True)
    borderless_windowing_run_wait = config_defaults.get('borderless_windowing_run_wait', False)
    multi_monitor_app_enabled = config_defaults.get('multi_monitor_app_enabled', True)
    multi_monitor_app_run_wait = config_defaults.get('multi_monitor_app_run_wait', False)
    just_after_launch_enabled = config_defaults.get('just_after_launch_enabled', True)
    just_after_launch_run_wait = config_defaults.get('just_after_launch_run_wait', False)
    just_before_exit_enabled = config_defaults.get('just_before_exit_enabled', True)
    just_before_exit_run_wait = config_defaults.get('just_before_exit_run_wait', False)
    pre1_enabled = config_defaults.get('pre_1_enabled', True)
    post1_enabled = config_defaults.get('post_1_enabled', True)
    pre2_enabled = config_defaults.get('pre_2_enabled', True)
    post2_enabled = config_defaults.get('post_2_enabled', True)
    pre3_enabled = config_defaults.get('pre_3_enabled', True)
    post3_enabled = config_defaults.get('post_3_enabled', True)
    pre1_run_wait = config_defaults.get('pre_1_run_wait', False)
    post1_run_wait = config_defaults.get('post_1_run_wait', False)
    pre2_run_wait = config_defaults.get('pre_2_run_wait', False)
    post2_run_wait = config_defaults.get('post_2_run_wait', False)
    pre3_run_wait = config_defaults.get('pre_3_run_wait', False)
    post3_run_wait = config_defaults.get('post_3_run_wait', False)

    # Create checkboxes for Controller Mapper
    main_window.editor_table.setCellWidget(row, constants.EditorCols.CM_ENABLED.value, create_status_widget(main_window, controller_mapper_enabled, row, constants.EditorCols.CM_ENABLED.value))
    main_window.editor_table.setCellWidget(row, constants.EditorCols.CM_RUN_WAIT.value, create_status_widget(main_window, controller_mapper_run_wait, row, constants.EditorCols.CM_RUN_WAIT.value))

    # Create checkboxes for Borderless Windowing
    main_window.editor_table.setCellWidget(row, constants.EditorCols.BW_ENABLED.value, create_status_widget(main_window, borderless_windowing_enabled, row, constants.EditorCols.BW_ENABLED.value))
    main_window.editor_table.setCellWidget(row, constants.EditorCols.BW_RUN_WAIT.value, create_status_widget(main_window, borderless_windowing_run_wait, row, constants.EditorCols.BW_RUN_WAIT.value))

    # Create checkboxes for Multi-Monitor App
    main_window.editor_table.setCellWidget(row, constants.EditorCols.MM_ENABLED.value, create_status_widget(main_window, multi_monitor_app_enabled, row, constants.EditorCols.MM_ENABLED.value))
    main_window.editor_table.setCellWidget(row, constants.EditorCols.MM_RUN_WAIT.value, create_status_widget(main_window, multi_monitor_app_run_wait, row, constants.EditorCols.MM_RUN_WAIT.value))

    # Column 17 is Hide Taskbar (checkbox created later)

    # Create checkboxes for Just After Launch
    main_window.editor_table.setCellWidget(row, constants.EditorCols.JA_ENABLED.value, create_status_widget(main_window, just_after_launch_enabled, row, constants.EditorCols.JA_ENABLED.value))
    main_window.editor_table.setCellWidget(row, constants.EditorCols.JA_RUN_WAIT.value, create_status_widget(main_window, just_after_launch_run_wait, row, constants.EditorCols.JA_RUN_WAIT.value))

    # Create checkboxes for Just Before Exit
    main_window.editor_table.setCellWidget(row, constants.EditorCols.JB_ENABLED.value, create_status_widget(main_window, just_before_exit_enabled, row, constants.EditorCols.JB_ENABLED.value))
    main_window.editor_table.setCellWidget(row, constants.EditorCols.JB_RUN_WAIT.value, create_status_widget(main_window, just_before_exit_run_wait, row, constants.EditorCols.JB_RUN_WAIT.value))

    # Pre/Post default enabled/run-wait checkboxes
    main_window.editor_table.setCellWidget(row, constants.EditorCols.PRE1_ENABLED.value, create_status_widget(main_window, pre1_enabled, row, constants.EditorCols.PRE1_ENABLED.value))
    main_window.editor_table.setCellWidget(row, constants.EditorCols.PRE1_RUN_WAIT.value, create_status_widget(main_window, pre1_run_wait, row, constants.EditorCols.PRE1_RUN_WAIT.value))

    main_window.editor_table.setCellWidget(row, constants.EditorCols.POST1_ENABLED.value, create_status_widget(main_window, post1_enabled, row, constants.EditorCols.POST1_ENABLED.value))
    main_window.editor_table.setCellWidget(row, constants.EditorCols.POST1_RUN_WAIT.value, create_status_widget(main_window, post1_run_wait, row, constants.EditorCols.POST1_RUN_WAIT.value))

    main_window.editor_table.setCellWidget(row, constants.EditorCols.PRE2_ENABLED.value, create_status_widget(main_window, pre2_enabled, row, constants.EditorCols.PRE2_ENABLED.value))
    main_window.editor_table.setCellWidget(row, constants.EditorCols.PRE2_RUN_WAIT.value, create_status_widget(main_window, pre2_run_wait, row, constants.EditorCols.PRE2_RUN_WAIT.value))

    main_window.editor_table.setCellWidget(row, constants.EditorCols.POST2_ENABLED.value, create_status_widget(main_window, post2_enabled, row, constants.EditorCols.POST2_ENABLED.value))
    main_window.editor_table.setCellWidget(row, constants.EditorCols.POST2_RUN_WAIT.value, create_status_widget(main_window, post2_run_wait, row, constants.EditorCols.POST2_RUN_WAIT.value))

    main_window.editor_table.setCellWidget(row, constants.EditorCols.PRE3_ENABLED.value, create_status_widget(main_window, pre3_enabled, row, constants.EditorCols.PRE3_ENABLED.value))
    main_window.editor_table.setCellWidget(row, constants.EditorCols.PRE3_RUN_WAIT.value, create_status_widget(main_window, pre3_run_wait, row, constants.EditorCols.PRE3_RUN_WAIT.value))

    main_window.editor_table.setCellWidget(row, constants.EditorCols.POST3_ENABLED.value, create_status_widget(main_window, post3_enabled, row, constants.EditorCols.POST3_ENABLED.value))
    main_window.editor_table.setCellWidget(row, constants.EditorCols.POST3_RUN_WAIT.value, create_status_widget(main_window, post3_run_wait, row, constants.EditorCols.POST3_RUN_WAIT.value))

    # Create RunAsAdmin checkbox
    as_admin_widget = create_status_widget(main_window, as_admin, row, constants.EditorCols.RUN_AS_ADMIN.value)
    main_window.editor_table.setCellWidget(row, constants.EditorCols.RUN_AS_ADMIN.value, as_admin_widget)
    
    # Create HideTaskbar checkbox
    hide_taskbar_widget = create_status_widget(main_window, no_tb, row, constants.EditorCols.HIDE_TASKBAR.value)
    main_window.editor_table.setCellWidget(row, constants.EditorCols.HIDE_TASKBAR.value, hide_taskbar_widget)
    # Update UI if requested
    if update_ui:
        QCoreApplication.processEvents()
    
    return row

def create_status_widget(main_window, is_checked=False, row=-1, col=-1):
    """Create a checkbox widget for table cells"""
    checkbox = QCheckBox()
    checkbox.setChecked(is_checked)
    checkbox.setStyleSheet("QCheckBox { margin-left: 10px; }")
    
    # Center the checkbox in the cell
    container = QWidget()
    layout = QHBoxLayout(container)
    layout.addWidget(checkbox)
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.setContentsMargins(0, 0, 0, 0)
    container.setLayout(layout)
    
    # Store row and column for callback purposes
    if row >= 0 and col >= 0:
        checkbox.row = row
        checkbox.col = col
        
        # Connect to parent's edited handler if available
        if hasattr(main_window, '_on_editor_table_edited'):
            checkbox.stateChanged.connect(lambda state: main_window._on_editor_table_edited(QTableWidgetItem()))
    
    return container
