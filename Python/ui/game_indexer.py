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
    include_widget = create_status_widget(main_window, include_checked, row, 0)
    main_window.editor_table.setCellWidget(row, 0, include_widget)

    # Retrieve global default enabled states from AppConfig
    config_defaults = main_window.config.defaults
    as_admin = main_window.config.run_as_admin # From Deployment tab
    no_tb = main_window.config.hide_taskbar # From Deployment tab
    
    # Set text items
    main_window.editor_table.setItem(row, 1, QTableWidgetItem(exec_name))
    main_window.editor_table.setItem(row, 2, QTableWidgetItem(directory))
    main_window.editor_table.setItem(row, 3, QTableWidgetItem(steam_name))
    main_window.editor_table.setItem(row, 4, QTableWidgetItem(name_override))
    main_window.editor_table.setItem(row, 5, QTableWidgetItem(options))
    main_window.editor_table.setItem(row, 6, QTableWidgetItem(arguments))
    main_window.editor_table.setItem(row, 7, QTableWidgetItem(steam_id))
    
    # Get deployment tab settings to populate path fields with CEN/LC indicators
    # These columns correspond to path fields in the Setup Tab.
    path_columns = {
        # These keys match the `line_edit_attr` from `_create_path_row_with_cen_lc` in setup_tab.py
        12: "multimonitor_gaming_config_edit",
        13: "multimonitor_media_config_edit",
        14: "p1_profile_edit",
        15: "p2_profile_edit",
        16: "mediacenter_profile_edit",
        20: "pre1_edit",
        22: "post1_edit",
        24: "pre2_edit",
        26: "post2_edit",
        28: "pre3_edit",
    }
    
    # Check if deployment_path_options exists
    if hasattr(main_window, 'deployment_path_options'):
        for col, path_key in path_columns.items():
            snake_case_key = to_snake_case(path_key.replace("_edit", "").replace("_app", ""))

            # Default to CEN
            indicator = "<"
            
            # Check if we have a radio group for this path
            if snake_case_key in main_window.deployment_path_options:
                radio_group = main_window.deployment_path_options[snake_case_key]
                checked_button = radio_group.checkedButton()
                if checked_button and checked_button.text() == "LC":
                    indicator = ">"

            main_window.editor_table.setItem(row, col, QTableWidgetItem(indicator))
    else:
        # If no deployment_path_options, default all to CEN
        for col in path_columns.keys():
            main_window.editor_table.setItem(row, col, QTableWidgetItem("<"))
    
    # Retrieve default enabled states for specific features from config.defaults
    controller_mapper_enabled = config_defaults.get('controller_mapper_enabled', True)
    borderless_windowing_enabled = config_defaults.get('borderless_windowing_enabled', True)
    multi_monitor_app_enabled = config_defaults.get('multi_monitor_app_enabled', True)
    just_after_launch_enabled = config_defaults.get('just_after_launch_enabled', True)
    just_before_exit_enabled = config_defaults.get('just_before_exit_enabled', True)
    pre1_enabled = config_defaults.get('pre_1_enabled', True)
    post1_enabled = config_defaults.get('post_1_enabled', True)
    pre2_enabled = config_defaults.get('pre_2_enabled', True)
    post2_enabled = config_defaults.get('post_2_enabled', True)
    pre3_enabled = config_defaults.get('pre_3_enabled', True)
    post3_enabled = config_defaults.get('post_3_enabled', True)

    # Create checkboxes for the new enabled columns
    main_window.editor_table.setCellWidget(row, 8, create_status_widget(main_window, controller_mapper_enabled, row, 8))
    main_window.editor_table.setCellWidget(row, 9, create_status_widget(main_window, borderless_windowing_enabled, row, 9))
    main_window.editor_table.setCellWidget(row, 10, create_status_widget(main_window, multi_monitor_app_enabled, row, 10))
    
    # Column 11 is Hide Taskbar, handled below
    # Columns 12-16 are profile paths, their CEN/LC indicators are handled above

    main_window.editor_table.setCellWidget(row, 17, create_status_widget(main_window, just_after_launch_enabled, row, 17))
    main_window.editor_table.setCellWidget(row, 18, create_status_widget(main_window, just_before_exit_enabled, row, 18))
    
    main_window.editor_table.setCellWidget(row, 19, create_status_widget(main_window, pre1_enabled, row, 19))
    # The text field for Pre1 (col 20) is set by the CEN/LC logic above

    main_window.editor_table.setCellWidget(row, 21, create_status_widget(main_window, post1_enabled, row, 21))
    # The text field for Post1 (col 22) is set by the CEN/LC logic above

    main_window.editor_table.setCellWidget(row, 23, create_status_widget(main_window, pre2_enabled, row, 23))
    # The text field for Pre2 (col 24) is set by the CEN/LC logic above

    main_window.editor_table.setCellWidget(row, 25, create_status_widget(main_window, post2_enabled, row, 25))
    # The text field for Post2 (col 26) is set by the CEN/LC logic above

    main_window.editor_table.setCellWidget(row, 27, create_status_widget(main_window, pre3_enabled, row, 27))
    # The text field for Pre3 (col 28) is set by the CEN/LC logic above

    main_window.editor_table.setCellWidget(row, 29, create_status_widget(main_window, post3_enabled, row, 29))
    # No text field for Post3 in the current editor_tab.py, so column 30 is not used for a text item.

    # Create AsAdmin checkbox
    as_admin_widget = create_status_widget(main_window, as_admin, row, 22)
    main_window.editor_table.setCellWidget(row, 22, as_admin_widget)
    
    # Create NoTB checkbox
    no_tb_widget = create_status_widget(main_window, no_tb, row, 23)
    main_window.editor_table.setCellWidget(row, 23, no_tb_widget)
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
