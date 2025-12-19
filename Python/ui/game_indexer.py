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
from Python.ui.name_utils import normalize_name_for_matching, make_safe_filename
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
                        
                        # Add to the editor table
                        row_position = main_window.editor_table.rowCount()
                        main_window.editor_table.insertRow(row_position)
                        
                        # Create a checkbox for the Include column
                        include_checkbox = QCheckBox()
                        include_checkbox.setChecked(include_by_default)  # Set based on our determination
                        include_checkbox_widget = QWidget()
                        include_checkbox_layout = QHBoxLayout(include_checkbox_widget)
                        include_checkbox_layout.addWidget(include_checkbox)
                        include_checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        include_checkbox_layout.setContentsMargins(0, 0, 0, 0)
                        
                        # Set the items in the table
                        main_window.editor_table.setCellWidget(row_position, 0, include_checkbox_widget)
                        main_window.editor_table.setItem(row_position, 1, QTableWidgetItem(exec_name))
                        main_window.editor_table.setItem(row_position, 2, QTableWidgetItem(dir_path))
                        main_window.editor_table.setItem(row_position, 3, QTableWidgetItem(steam_name))
                        main_window.editor_table.setItem(row_position, 4, QTableWidgetItem(name_override))
                        main_window.editor_table.setItem(row_position, 5, QTableWidgetItem(""))
                        main_window.editor_table.setItem(row_position, 6, QTableWidgetItem(""))
                        main_window.editor_table.setItem(row_position, 7, QTableWidgetItem(steam_id))
                        
                        # Get deployment tab settings to populate path fields with CEN/LC indicators
                        # Columns 8-20 are path fields that should use < for CEN and > for LC
                        path_columns = {
                            8: "p1_profile_edit",
                            9: "p2_profile_edit",
                            10: "controller_mapper_app_line_edit",
                            11: "multimonitor_gaming_config_edit",
                            12: "multimonitor_media_config_edit",
                            13: "post_launch_app_line_edit_0",
                            14: "post_launch_app_line_edit_1",
                            15: "post_launch_app_line_edit_2",
                            16: "pre_launch_app_line_edit_0",
                            17: "pre_launch_app_line_edit_1",
                            18: "pre_launch_app_line_edit_2",
                            19: "after_launch_app_line_edit",
                            20: "before_exit_app_line_edit"
                        }
                        
                        # Check if deployment_path_options exists
                        if hasattr(main_window, 'deployment_path_options'):
                            for col, path_key in path_columns.items():
                                # Default to CEN
                                indicator = "<"
                                
                                # Check if we have a radio group for this path
                                if path_key in main_window.deployment_path_options:
                                    radio_group = main_window.deployment_path_options[path_key]
                                    checked_button = radio_group.checkedButton()
                                    if checked_button and checked_button.text() == "LC":
                                        indicator = ">"
                            
                                main_window.editor_table.setItem(row_position, col, QTableWidgetItem(indicator))
                        else:
                            # If no deployment_path_options, default all to CEN
                            for col in range(8, 21):
                                main_window.editor_table.setItem(row_position, col, QTableWidgetItem("<"))
                        
                        # Set borderless status (E for enabled, K for terminates on exit, blank for not enabled)
                        borderless_value = ""
                        if hasattr(main_window, 'enable_borderless_windowing_checkbox') and main_window.enable_borderless_windowing_checkbox.isChecked():
                            borderless_value = "E"
                            if hasattr(main_window, 'terminate_bw_on_exit_checkbox') and main_window.terminate_bw_on_exit_checkbox.isChecked():
                                borderless_value = "K"
                        main_window.editor_table.setItem(row_position, 21, QTableWidgetItem(borderless_value))
                        
                        # Use deployment tab settings for AsAdmin and NoTB if not explicitly provided
                        as_admin = False
                        if hasattr(main_window, 'run_as_admin_checkbox'):
                            as_admin = main_window.run_as_admin_checkbox.isChecked()
                        
                        no_tb = False
                        if hasattr(main_window, 'hide_taskbar_checkbox'):
                            no_tb = main_window.hide_taskbar_checkbox.isChecked()
                        
                        # Create AsAdmin checkbox
                        as_admin_widget = create_status_widget(main_window, as_admin, row_position, 22)
                        main_window.editor_table.setCellWidget(row_position, 22, as_admin_widget)
                        
                        # Create NoTB checkbox
                        no_tb_widget = create_status_widget(main_window, no_tb, row_position, 23)
                        main_window.editor_table.setCellWidget(row_position, 23, no_tb_widget)
                        
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

def get_editor_table_data(editor_table):
    """Extract data from the editor table into a list of dictionaries"""
    data = []
    for row in range(editor_table.rowCount()):
        # Get checkbox values safely
        def get_checkbox_value(row, col):
            widget = editor_table.cellWidget(row, col)
            if widget:
                # Find the checkbox within the container widget
                checkbox = widget.findChild(QCheckBox)
                if checkbox:
                    return checkbox.isChecked()
            return False
        
        # Get borderless value from combo box or text item
        borderless_widget = editor_table.cellWidget(row, 21)
        borderless_item = editor_table.item(row, 21)
        
        if isinstance(borderless_widget, QComboBox):
            borderless_value = borderless_widget.currentText()
        elif borderless_item:
            borderless_value = borderless_item.text()
        else:
            borderless_value = "No"
        
        # Get CEN/LC indicators for path fields
        path_indicators = {}
        for col in range(8, 21):
            item = editor_table.item(row, col)
            if item:
                indicator = item.text()
                # Store the indicator (< for CEN, > for LC)
                path_indicators[f"col_{col}_indicator"] = indicator
        
        row_data = {
            "include": get_checkbox_value(row, 0),
            "executable": editor_table.item(row, 1).text() if editor_table.item(row, 1) else "",
            "directory": editor_table.item(row, 2).text() if editor_table.item(row, 2) else "",
            "steam_title": editor_table.item(row, 3).text() if editor_table.item(row, 3) else "",
            "name_override": editor_table.item(row, 4).text() if editor_table.item(row, 4) else "",
            "options": editor_table.item(row, 5).text() if editor_table.item(row, 5) else "",
            "arguments": editor_table.item(row, 6).text() if editor_table.item(row, 6) else "",
            "steam_id": editor_table.item(row, 7).text() if editor_table.item(row, 7) else "",
            "p1_profile": editor_table.item(row, 8).text() if editor_table.item(row, 8) else "",
            "p2_profile": editor_table.item(row, 9).text() if editor_table.item(row, 9) else "",
            "desktop_ctrl": editor_table.item(row, 10).text() if editor_table.item(row, 10) else "",
            "game_monitor_cfg": editor_table.item(row, 11).text() if editor_table.item(row, 11) else "",
            "desktop_monitor_cfg": editor_table.item(row, 12).text() if editor_table.item(row, 12) else "",
            "post1": editor_table.item(row, 13).text() if editor_table.item(row, 13) else "",
            "post2": editor_table.item(row, 14).text() if editor_table.item(row, 14) else "",
            "post3": editor_table.item(row, 15).text() if editor_table.item(row, 15) else "",
            "pre1": editor_table.item(row, 16).text() if editor_table.item(row, 16) else "",
            "pre2": editor_table.item(row, 17).text() if editor_table.item(row, 17) else "",
            "pre3": editor_table.item(row, 18).text() if editor_table.item(row, 18) else "",
            "just_after": editor_table.item(row, 19).text() if editor_table.item(row, 19) else "",
            "just_before": editor_table.item(row, 20).text() if editor_table.item(row, 20) else "",
            "borderless": borderless_value,
            "as_admin": get_checkbox_value(row, 22),
            "no_tb": get_checkbox_value(row, 23),
            "path_indicators": path_indicators  # Store all path indicators
        }
        data.append(row_data)
    return data

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
    Add an executable to the editor table
    
    Args:
        main_window: The main application window
        include_checked: Whether the include checkbox should be checked
        exec_name: The executable name
        directory: The directory path
        steam_name: The Steam name
        name_override: The name override
        options: Additional options
        arguments: Command line arguments
        steam_id: The Steam ID
        as_admin: Whether to run as admin
        no_tb: Whether to disable taskbar integration
        update_ui: Whether to update the UI after adding
    """
    # Debug output



    
    # Get current row count
    row = main_window.editor_table.rowCount()
    main_window.editor_table.insertRow(row)
    
    # Create include checkbox
    include_widget = create_status_widget(main_window, include_checked, row, 0)
    main_window.editor_table.setCellWidget(row, 0, include_widget)
    
    # Set text items
    main_window.editor_table.setItem(row, 1, QTableWidgetItem(exec_name))
    main_window.editor_table.setItem(row, 2, QTableWidgetItem(directory))
    main_window.editor_table.setItem(row, 3, QTableWidgetItem(steam_name))
    main_window.editor_table.setItem(row, 4, QTableWidgetItem(name_override))
    main_window.editor_table.setItem(row, 5, QTableWidgetItem(options))
    main_window.editor_table.setItem(row, 6, QTableWidgetItem(arguments))
    main_window.editor_table.setItem(row, 7, QTableWidgetItem(steam_id))
    
    # Get deployment tab settings to populate path fields with CEN/LC indicators
    # Columns 8-20 are path fields that should use < for CEN and > for LC
    path_columns = {
        8: "p1_profile_edit",
        9: "p2_profile_edit",
        10: "controller_mapper_app_line_edit",
        11: "multimonitor_gaming_config_edit",
        12: "multimonitor_media_config_edit",
        13: "post_launch_app_line_edit_0",
        14: "post_launch_app_line_edit_1",
        15: "post_launch_app_line_edit_2",
        16: "pre_launch_app_line_edit_0",
        17: "pre_launch_app_line_edit_1",
        18: "pre_launch_app_line_edit_2",
        19: "after_launch_app_line_edit",
        20: "before_exit_app_line_edit"
    }
    
    # Check if deployment_path_options exists
    if hasattr(main_window, 'deployment_path_options'):
        for col, path_key in path_columns.items():
            # Default to CEN
            indicator = "<"
            
            # Check if we have a radio group for this path
            if path_key in main_window.deployment_path_options:
                radio_group = main_window.deployment_path_options[path_key]
                checked_button = radio_group.checkedButton()
                if checked_button and checked_button.text() == "LC":
                    indicator = ">"
            
            main_window.editor_table.setItem(row, col, QTableWidgetItem(indicator))
    else:
        # If no deployment_path_options, default all to CEN
        for col in range(8, 21):
            main_window.editor_table.setItem(row, col, QTableWidgetItem("<"))
    
    # Set borderless status (E for enabled, K for terminates on exit, blank for not enabled)
    borderless_value = ""
    if hasattr(main_window, 'enable_borderless_windowing_checkbox') and main_window.enable_borderless_windowing_checkbox.isChecked():
        borderless_value = "E"
        if hasattr(main_window, 'terminate_bw_on_exit_checkbox') and main_window.terminate_bw_on_exit_checkbox.isChecked():
            borderless_value = "K"
    main_window.editor_table.setItem(row, 21, QTableWidgetItem(borderless_value))
    
    # Use deployment tab settings for AsAdmin and NoTB if not explicitly provided
    if not as_admin and hasattr(main_window, 'run_as_admin_checkbox'):
        as_admin = main_window.run_as_admin_checkbox.isChecked()
    
    if not no_tb and hasattr(main_window, 'hide_taskbar_checkbox'):
        no_tb = main_window.hide_taskbar_checkbox.isChecked()
    
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
