from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QStatusBar, 
    QMessageBox, QMenu, QFileDialog, QTableWidgetItem, QCheckBox,
    QProgressDialog, QVBoxLayout, QHBoxLayout, QHeaderView, QMessageBox, QInputDialog
)
from PyQt6.QtCore import Qt, QCoreApplication, pyqtSlot, QEvent, QObject
from PyQt6.QtGui import QCursor
import urllib.request
import urllib.error
import shutil
import os
import time
import threading

import requests
# Import tab population functions
from Python.setup_tab import SetupTab
from Python.ui.setup_tab_ui import populate_setup_tab
from Python.ui.deployment_tab import DeploymentTab
from Python.ui.editor_tab_ui import populate_editor_tab
from Python.ui.steam_cache import SteamCacheManager, STEAM_FILTERED_TXT, NORMALIZED_INDEX_CACHE
from Python.ui.editor_tab import EditorTab
from Python.models import AppConfig
from Python import config_manager
from Python import constants
import logging

class _StatusUpdateEvent(QEvent):
    """Custom event for updating the status bar message."""
    def __init__(self, message, timeout=0):
        super().__init__(QEvent.Type(QEvent.Type.User + 1))
        self.message = message
        self.timeout = timeout

class _ProcessPromptEvent(QEvent):
    """Custom event to prompt for processing a file."""
    def __init__(self, file_path):
        super().__init__(QEvent.Type(QEvent.Type.User + 2))
        self.file_path = file_path

class _EnableUIEvent(QEvent):
    """Custom event to re-enable UI elements."""
    def __init__(self):
        super().__init__(QEvent.Type(QEvent.Type.User + 3))


class DataManager:
    """Manages data indexing, loading, and saving operations."""
    def __init__(self, main_window):
        self.main_window = main_window
        self.config = main_window.config
        self._load_set_files()

    def _load_set_files(self):
        """Load set files into memory."""
        from Python.ui.game_indexer import load_set_file
        self.release_groups_set = load_set_file(constants.RELEASE_GROUPS_SET)
        self.folder_exclude_set = load_set_file(constants.FOLDER_EXCLUDE_SET)
        self.exclude_exe_set = load_set_file(constants.EXCLUDE_EXE_SET)
        self.demoted_set = load_set_file(constants.DEMOTED_SET)
        self.folder_demoted_set = load_set_file(constants.FOLDER_DEMOTED_SET)

    def index_sources(self):
        """Index source directories and save to current.index."""
        from Python.ui.game_indexer import index_games
        from Python.ui.index_manager import save_index
        
        self.main_window.statusBar().showMessage("Indexing source directories...", 0)
        
        found_count = index_games(
            self.main_window,
            source_dirs=self.config.source_dirs,
            excluded_dirs=self.config.excluded_dirs,
            exclude_exe_set=self.exclude_exe_set,
            folder_exclude_set=self.folder_exclude_set,
            demoted_set=self.demoted_set,
            folder_demoted_set=self.folder_demoted_set,
            release_groups_set=self.release_groups_set,
            enable_name_matching=self.config.enable_name_matching
        )
        
        if found_count > 0:
            data = self.main_window.editor_tab.get_all_game_data()
            save_index(self.main_window, constants.APP_ROOT_DIR, data)
        
        self.main_window.statusBar().showMessage(f"Indexed {found_count} executables", 5000)

    def load_index(self):
        """Load an index file into the editor table."""
        from Python.ui.index_manager import load_index
        data = load_index(self.main_window, constants.APP_ROOT_DIR, prompt_for_filename=True)
        if data:
            self.main_window.editor_tab.populate_from_data(data)
            self.main_window.statusBar().showMessage(f"Loaded {len(data)} entries from index.", 3000)
            return True
        return False

    def save_editor_table_to_index(self):
        """Save the editor table data to an index file."""
        from Python.ui.index_manager import save_index
        data = self.main_window.editor_tab.get_all_game_data()
        saved_path = save_index(self.main_window, constants.APP_ROOT_DIR, data)
        if saved_path:
            self.main_window.statusBar().showMessage(f"Index saved to {os.path.basename(saved_path)}", 3000)
            return True
        return False

    def delete_indexes(self):
        """Delete all index files with confirmation."""
        reply = QMessageBox.question(self.main_window, "Confirm Delete", "Are you sure you want to delete all index files?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            from Python.ui.index_manager import delete_all_indexes
            deleted_count = delete_all_indexes(constants.APP_ROOT_DIR)
            self.main_window.statusBar().showMessage(f"{deleted_count} index files deleted", 3000)

class SteamManager:
    """Manages Steam data operations like downloading and processing JSON."""
    def __init__(self, main_window):
        self.main_window = main_window
        self.steam_cache_manager = main_window.steam_cache_manager
        self.download_thread = None
        self.is_downloading = False

    def download_steam_json(self, version=2):
        """Download the Steam JSON file with progress tracking."""
        if self.is_downloading:
            self.main_window.statusBar().showMessage("Download already in progress", 3000)
            return

        # Confirm overwrite if file exists
        output_file = constants.STEAM_JSON_FILE
        if os.path.exists(output_file):
            reply = QMessageBox.question(self.main_window, "Confirm Overwrite",
                                         f"The file 'steam.json' already exists. Are you sure you want to download and replace it?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                return

        url = None
        repos_file = constants.REPOS_SET
        try:
            if os.path.exists(repos_file):
                with open(repos_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if version == 1 and "STEAMJSON1" in line:
                            url = line.split("=")[1].strip()
                            break
                        elif version == 2 and "STEAMJSON2" in line:
                            url = line.split("=")[1].strip()
                            break
        except Exception as e:
            logging.error(f"Could not read repos.set file: {e}")

        if not url:
            url = f"http://api.steampowered.com/ISteamApps/GetAppList/v{version}/?format=json"

        if os.path.exists(output_file):
            backup_file = output_file + ".old"
            if os.path.exists(backup_file):
                os.remove(backup_file)
            shutil.copy2(output_file, backup_file)
            logging.info(f"Backed up existing '{os.path.basename(output_file)}' to '{os.path.basename(backup_file)}'")

        # Disable UI elements during download
        self._disable_ui_during_download()

        # Start download in a separate thread
        self.download_thread = threading.Thread(
            target=self._download_with_progress,
            args=(url, output_file, version)
        )
        self.download_thread.daemon = True
        self.download_thread.start()

    def _download_with_progress(self, url, output_file, version):
        """Download file with progress tracking."""
        self.is_downloading = True
        start_time = time.time()
    
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            with requests.get(url, headers=headers, stream=True) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                downloaded = 0
                
                with open(output_file, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            if total_size > 0:
                                percent = min(100, (downloaded * 100) / total_size)
                                elapsed_time = time.time() - start_time
                                if elapsed_time > 0:
                                    speed = downloaded / elapsed_time
                                    speed_mb = speed / (1024 * 1024)
                                    remaining = total_size - downloaded
                                    eta_seconds = remaining / speed if speed > 0 else 0
                                    eta_str = self._format_eta(eta_seconds)
                                    progress_text = f"Downloading Steam JSON (v{version}): {percent:.1f}% | {speed_mb:.2f} MB/s | ETA: {eta_str}"
                                else:
                                    progress_text = f"Downloading Steam JSON (v{version}): {percent:.1f}%"
                            else: # If no content-length, just show amount downloaded
                                downloaded_mb = downloaded / (1024 * 1024)
                                progress_text = f"Downloading Steam JSON (v{version}): {downloaded_mb:.2f} MB"
                            
                            QCoreApplication.postEvent(self.main_window, _StatusUpdateEvent(progress_text))
                        else:
                            # Handle case where chunk is empty
                            break
                        if self.main_window.isHidden(): # Check if window is closed
                            logging.warning("Main window closed during download. Aborting.")
                            raise Exception("Download aborted.")
                            
            # Check if download was successful
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                QCoreApplication.postEvent(self.main_window, _StatusUpdateEvent(f"Steam JSON (v{version}) downloaded successfully", 5000))

                # Ask user if they want to process (on main thread)
                QCoreApplication.postEvent(self.main_window, _ProcessPromptEvent(output_file))
            else:
                QCoreApplication.postEvent(self.main_window, _StatusUpdateEvent(f"Failed to download Steam JSON (v{version})", 5000))

        except requests.exceptions.RequestException as e:
            QCoreApplication.postEvent(self.main_window, _StatusUpdateEvent(f"Network error downloading Steam JSON: {str(e)}", 5000))
        except Exception as e:
            QCoreApplication.postEvent(self.main_window, _StatusUpdateEvent(f"Error downloading Steam JSON: {str(e)}", 5000))
        finally:
            self.is_downloading = False
            # Re-enable UI elements
            QCoreApplication.postEvent(self.main_window, _EnableUIEvent())

    def _format_eta(self, seconds):
        """Format ETA in human readable format."""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"

    def _disable_ui_during_download(self):
        """Disable UI elements during download."""
        # Disable the entire tab widget to prevent switching
        self.main_window.tabs.setEnabled(False)

    def _enable_ui_after_download(self):
        """Re-enable UI elements after download."""
        # Re-enable the tab widget
        self.main_window.tabs.setEnabled(True)
        # Also ensure all tabs are enabled (in case SteamProcessor disabled them)
        for i in range(self.main_window.tabs.count()):
            self.main_window.tabs.widget(i).setEnabled(True)

    def prompt_and_process_steam_json(self, file_path=None):
        """Prompt the user to select a Steam JSON file and process it."""
        from Python.ui.steam_processor import SteamProcessor
        
        # Check if steam_processor exists, if not create it
        if not hasattr(self, 'steam_processor'):
            self.steam_processor = SteamProcessor(self.main_window, self.steam_cache_manager)
        
        # Now that we're sure it exists, use it
        if file_path:
            self.steam_processor.start_processing(file_path)
        else:
            self.steam_processor.prompt_and_process_steam_json()

    def delete_steam_json(self):
        """Delete the Steam JSON file with confirmation."""
        reply = QMessageBox.question(self.main_window, "Delete Steam JSON", "Are you sure you want to delete steam.json?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            if os.path.exists(constants.STEAM_JSON_FILE):
                os.remove(constants.STEAM_JSON_FILE)
                self.main_window.statusBar().showMessage("Steam JSON file deleted", 3000)

    def process_existing_json(self):
        """Process the existing steam.json file with UI handling and confirmation."""
        # Disable UI immediately
        self._disable_ui_during_download()
        
        steam_json_path = constants.STEAM_JSON_FILE
        
        # Check if file exists
        if not os.path.exists(steam_json_path):
            self.main_window.statusBar().showMessage("steam.json not found.", 5000)
            self._enable_ui_after_download()
            return

        # Check if cache files exist
        filtered_cache = os.path.join(constants.APP_ROOT_DIR, STEAM_FILTERED_TXT)
        normalized_cache = os.path.join(constants.APP_ROOT_DIR, NORMALIZED_INDEX_CACHE)
        
        should_prompt = False
        if os.path.exists(filtered_cache) or os.path.exists(normalized_cache):
            should_prompt = True
            
            # Check file sizes - skip prompt if either file exists and is less than 100KB
            if os.path.exists(filtered_cache) and os.path.getsize(filtered_cache) < 102400:
                should_prompt = False
            elif os.path.exists(normalized_cache) and os.path.getsize(normalized_cache) < 102400:
                should_prompt = False

        if should_prompt:
            reply = QMessageBox.question(
                self.main_window,
                "Confirm Processing",
                "This will overwrite/delete existing Steam cache files. Are you sure you want to proceed?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                self._enable_ui_after_download()
                return

        # Ensure processor exists and start processing
        if not hasattr(self, 'steam_processor'):
            from Python.ui.steam_processor import SteamProcessor
            self.steam_processor = SteamProcessor(self.main_window, self.steam_cache_manager)
        
        self.steam_processor.start_processing(steam_json_path)

class MainWindow(QMainWindow):
    def __init__(self):
        """Initialize the main window"""
        super().__init__()
        
        # Create the central configuration data model
        self.config = AppConfig()
        
        # Initialize managers that don't depend on the UI
        self.data_manager = DataManager(self)
        self.steam_cache_manager = SteamCacheManager(self)
        self.steam_manager = SteamManager(self)
        
        # Set up the UI
        self._setup_ui()
        
        # Load configuration into the data model
        config_manager.load_configuration(self.config)
        
        # Sync the UI to reflect the loaded configuration
        self.sync_ui_from_config()
        
        # Show the window
        self.show()

    def _load_steam_cache(self):
        """Load Steam cache from files"""
        # Load filtered Steam cache
        self.steam_cache_manager.load_filtered_steam_cache()
        
        # Load normalized Steam index
        self.steam_cache_manager.load_normalized_steam_index()
        
    def _setup_ui(self):
        self.setWindowTitle("Game Environment Manager")
        self.setGeometry(100, 100, 740, 240)  # Reduced from 950, 750 to 800, 600

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Create all tab widgets first
        self.setup_tab = SetupTab()
        self.deployment_tab = DeploymentTab()
        self.editor_tab = EditorTab(self)
        # Add tabs to the tab widget
        self.tabs.addTab(self.setup_tab, "Setup")
        self.tabs.addTab(self.deployment_tab, "Deployment")
        self.tabs.addTab(self.editor_tab, "Editor")

        # Note: SetupTab is the class-based implementation with full UI features.
        # populate_setup_tab() is the alternative function-based implementation.
        # Only use one or the other, not both.
        populate_setup_tab(self)
        self._connect_setup_tab_signals()

        # Highlight unpopulated items in deployment tab with red color
        self.deployment_tab.highlight_unpopulated_items(self)

        # Connect the setup tab's signal to our save logic
        self.setup_tab.config_changed.connect(self._sync_config_from_ui_and_save)
        
        # Connect the deployment tab's signals
        self.deployment_tab.config_changed.connect(self._sync_config_from_ui_and_save)
        self.deployment_tab.index_sources_requested.connect(self.data_manager.index_sources)
        self.deployment_tab.create_selected_requested.connect(self.on_create_button_clicked)
        self.deployment_tab.download_steam_json_requested.connect(self.steam_manager.download_steam_json)
        self.deployment_tab.delete_steam_json_requested.connect(self.steam_manager.delete_steam_json)
        self.deployment_tab.delete_steam_cache_requested.connect(self.steam_cache_manager.delete_cache_files)
        self.deployment_tab.process_steam_json_requested.connect(self.steam_manager.process_existing_json)

        # Connect the editor tab's signals
        self.editor_tab.save_index_requested.connect(self._save_editor_table_to_index)
        self.editor_tab.load_index_requested.connect(self._load_index)
        self.editor_tab.delete_indexes_requested.connect(self._on_delete_indexes)
        self.editor_tab.clear_view_requested.connect(self._on_clear_listview)
        
        # Create status bar
        self.statusBar().showMessage("Ready")

        # Install event filter for custom events
        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        """Handle custom events for thread-safe UI updates."""
        if event.type() == QEvent.Type.User + 1:  # _StatusUpdateEvent
            self.statusBar().showMessage(event.message, event.timeout)
            return True
        elif event.type() == QEvent.Type.User + 2:  # _ProcessPromptEvent
            reply = QMessageBox.question(self, "Process Steam JSON", "Do you want to process it now?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.Yes)
            if reply == QMessageBox.StandardButton.Yes:
                self.steam_manager.steam_cache_manager.backup_cache_files()
                self.steam_manager.prompt_and_process_steam_json(event.file_path)
            return True
        elif event.type() == QEvent.Type.User + 3:  # _EnableUIEvent
            self.steam_manager._enable_ui_after_download()
            return True
        return super().eventFilter(obj, event)

    def _connect_setup_tab_signals(self):
        """Connect signals from Setup Tab widgets to save logic."""
        widgets_to_connect = [
            getattr(self, 'exclude_manager_checkbox', None),
            getattr(self, 'after_launch_run_wait_checkbox', None),
            getattr(self, 'before_exit_run_wait_checkbox', None)
        ]
        
        # Add run-wait checkboxes
        if hasattr(self, 'pre_launch_run_wait_checkboxes'):
            widgets_to_connect.extend(self.pre_launch_run_wait_checkboxes)
        if hasattr(self, 'post_launch_run_wait_checkboxes'):
            widgets_to_connect.extend(self.post_launch_run_wait_checkboxes)
            
        for widget in widgets_to_connect:
            if widget:
                widget.clicked.connect(self._sync_config_from_ui_and_save)
        
        # Connect line edits to save on editing finished
        line_edits = [
            getattr(self, 'profiles_dir_edit', None),
            getattr(self, 'launchers_dir_edit', None),
            getattr(self, 'controller_mapper_app_line_edit', None),
            getattr(self, 'borderless_app_line_edit', None),
            getattr(self, 'multimonitor_app_line_edit', None),
            getattr(self, 'after_launch_app_line_edit', None),
            getattr(self, 'before_exit_app_line_edit', None),
            getattr(self, 'p1_profile_edit', None),
            getattr(self, 'p2_profile_edit', None),
            getattr(self, 'mediacenter_profile_edit', None),
            getattr(self, 'multimonitor_gaming_config_edit', None),
            getattr(self, 'multimonitor_media_config_edit', None),
        ]
        if hasattr(self, 'pre_launch_app_line_edits'):
            line_edits.extend(self.pre_launch_app_line_edits)
        if hasattr(self, 'post_launch_app_line_edits'):
            line_edits.extend(self.post_launch_app_line_edits)
            
        for le in line_edits:
            if le:
                le.editingFinished.connect(self._sync_config_from_ui_and_save)
                
        # Connect line edits and combos if needed, though they usually trigger on specific events or focus loss
        # For now, we rely on explicit save points or specific signals connected in populate_setup_tab
        # But we should ensure text changes in critical paths trigger updates if desired.
        # populate_setup_tab connects some buttons to methods, but not necessarily text changes to save.
        # We will rely on the user actions (Add/Remove) or explicit save for now, 
        # or add textChanged connections here if auto-save on type is desired.

    def _add_new_app_dialog(self, line_edit):
        """Handle the 'Add New...' option in app selection dropdowns"""
        # This is a placeholder for the actual implementation
        # It will be called when the user selects 'Add New...' in a dropdown
        pass
        
    def _add_to_combo(self, combo, title, is_directory=False):
        """Add an item to a combo box."""
        text = ""
        if is_directory:
            text = QFileDialog.getExistingDirectory(self, title)
        else:
            text, ok = QInputDialog.getText(self, title, "Enter item:")
            if not ok: return
            
        if text:
            if combo.findText(text) == -1:
                combo.addItem(text)
            combo.setCurrentText(text)
            self._sync_config_from_ui_and_save()

    def _remove_from_combo(self, combo):
        """Remove the current item from a combo box."""
        idx = combo.currentIndex()
        if idx >= 0:
            combo.removeItem(idx)
            self._sync_config_from_ui_and_save()

    def _update_steam_json_cache(self):
        """Update the Steam JSON cache"""
        # This method should update the Steam JSON cache
        self.statusBar().showMessage("Updating Steam JSON cache...", 5000)
        # In a real implementation, this would call a function to update the cache
        
    def _locate_and_exclude_manager_config(self):
        """Locate and exclude games from other managers' configurations"""
        from Python.ui.steam_utils import locate_and_exclude_manager_config
        locate_and_exclude_manager_config(self)
        
    def _load_index(self):
        """Load index file into editor table."""
        self.data_manager.load_index()
        
    def _save_editor_table_to_index(self):
        """Save the editor table data to an index file."""
        self.data_manager.save_editor_table_to_index()
        
    def _on_delete_indexes(self):
        """Handle request to delete index files."""
        self.data_manager.delete_indexes()
        
    def _on_clear_listview(self):
        """Clear the editor table"""
        self.editor_tab.table.setRowCount(0)
        self.statusBar().showMessage("List view cleared", 3000)
        
    def _regenerate_all_names(self):
        """Regenerate all name overrides in the table"""
        # This is a placeholder for the actual implementation
        # It will be called when the user clicks "Regenerate All Names" in the editor tab
        from Python.ui.name_processor import regenerate_all_names
        regenerate_all_names(self)
        self.statusBar().showMessage("All names regenerated", 3000)
        
    def _on_editor_table_cell_left_click(self, row, column):
        """Handle left-click on a cell in the editor table"""
        # This is a placeholder for the actual implementation
        # It will be called when the user left-clicks on a cell in the editor table
        pass
        
    def _on_editor_table_custom_context_menu(self, position):
        """Handle right-click on the editor table"""
        # This is a placeholder for the actual implementation
        # It will be called when the user right-clicks on the editor table
        context_menu = QMenu(self)
        
        # Add actions to the menu
        edit_action = context_menu.addAction("Edit")
        copy_action = context_menu.addAction("Copy")
        paste_action = context_menu.addAction("Paste")
        delete_action = context_menu.addAction("Delete")
        
        # Show the menu at the cursor position
        action = context_menu.exec(QCursor.pos())
        
        # Handle the selected action
        if action == edit_action:
            # Edit the selected row
            pass
        elif action == delete_action:
            # Delete the selected row
            pass
        
        if action == copy_action:
            # Copy the selected row
            pass
        
        if action == paste_action:
            # Paste the selected row
            pass
        
        
    def _on_editor_table_header_click(self, column):
        """Handle click on a header in the editor table"""
        # This is a placeholder for the actual implementation
        # It will be called when the user clicks on a header in the editor table
        pass
        
    def _on_editor_table_edited(self, item):
        """Called when the editor table is edited"""
        # Save the editor table data to the index file
        self._save_editor_table_to_index()
        
        # Update the status bar
        self.statusBar().showMessage("Editor table updated and saved", 3000)

    def _setup_creation_controller(self):
        """Initialize the creation controller"""
        from Python.ui.creation.creation_controller import CreationController
        self.creation_controller = CreationController(self)

    @pyqtSlot(str)
    def _on_logging_verbosity_changed(self, level_text):
        """Update the application's logging level based on the dropdown selection."""
        level_map = {
            "None": logging.CRITICAL + 1,  # A level higher than critical to disable most logging
            "Low": logging.WARNING,
            "Medium": logging.INFO,
            "High": logging.DEBUG,
            "Debug": logging.DEBUG
        }
        
        # Get the corresponding logging level, default to INFO
        log_level = level_map.get(level_text, logging.INFO)
        
        # Get the root logger and set its level
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # Log the change itself for confirmation
        logging.warning(f"Logging level changed to: {level_text} ({log_level})")
        self.statusBar().showMessage(f"Logging level set to {level_text}", 3000)

        # Update the model and save the configuration
        self.config.logging_verbosity = level_text
        config_manager.save_configuration(self.config)
        
    def sync_ui_from_config(self):
        """Updates the UI widgets with values from the AppConfig model."""
        # Sync Setup Tab widgets directly
        self._sync_setup_tab_ui_from_config(self.config)
        
        self.deployment_tab.sync_ui_from_config(self.config)
        
        # Apply visual settings (Theme/Font)
        self._apply_visual_settings()

    def _sync_setup_tab_ui_from_config(self, config):
        """Sync Setup Tab UI widgets from AppConfig."""
        # Source Configuration
        if hasattr(self, 'source_dirs_combo'):
            self.source_dirs_combo.clear()
            self.source_dirs_combo.addItems(config.source_dirs)
        if hasattr(self, 'exclude_items_combo'):
            self.exclude_items_combo.clear()
            self.exclude_items_combo.addItems(config.excluded_dirs)
        if hasattr(self, 'other_managers_combo'):
            self.other_managers_combo.setCurrentText(config.game_managers_present)
        if hasattr(self, 'exclude_manager_checkbox'):
            self.exclude_manager_checkbox.setChecked(config.exclude_selected_manager_games)
        if hasattr(self, 'logging_verbosity_combo'):
            self.logging_verbosity_combo.setCurrentText(config.logging_verbosity)
            
        # Directories
        if hasattr(self, 'profiles_dir_edit'): self.profiles_dir_edit.setText(config.profiles_dir)
        if hasattr(self, 'launchers_dir_edit'): self.launchers_dir_edit.setText(config.launchers_dir)
        
        # Applications
        if hasattr(self, 'controller_mapper_app_line_edit'): self.controller_mapper_app_line_edit.setText(config.controller_mapper_path)
        if hasattr(self, 'borderless_app_line_edit'): self.borderless_app_line_edit.setText(config.borderless_gaming_path)
        if hasattr(self, 'multimonitor_app_line_edit'): self.multimonitor_app_line_edit.setText(config.multi_monitor_tool_path)
        if hasattr(self, 'after_launch_app_line_edit'): self.after_launch_app_line_edit.setText(config.just_after_launch_path)
        if hasattr(self, 'before_exit_app_line_edit'): self.before_exit_app_line_edit.setText(config.just_before_exit_path)
        
        if hasattr(self, 'after_launch_run_wait_checkbox'): self.after_launch_run_wait_checkbox.setChecked(config.run_wait_states.get('just_after_launch_run_wait', False))
        if hasattr(self, 'before_exit_run_wait_checkbox'): self.before_exit_run_wait_checkbox.setChecked(config.run_wait_states.get('just_before_exit_run_wait', True))
        
        # Profiles
        if hasattr(self, 'p1_profile_edit'): self.p1_profile_edit.setText(config.p1_profile_path)
        if hasattr(self, 'p2_profile_edit'): self.p2_profile_edit.setText(config.p2_profile_path)
        if hasattr(self, 'mediacenter_profile_edit'): self.mediacenter_profile_edit.setText(config.mediacenter_profile_path)
        if hasattr(self, 'multimonitor_gaming_config_edit'): self.multimonitor_gaming_config_edit.setText(config.multimonitor_gaming_path)
        if hasattr(self, 'multimonitor_media_config_edit'): self.multimonitor_media_config_edit.setText(config.multimonitor_media_path)
        
        # Pre/Post Launch Apps
        if hasattr(self, 'pre_launch_app_line_edits'):
            paths = [config.pre1_path, config.pre2_path, config.pre3_path]
            for i, le in enumerate(self.pre_launch_app_line_edits):
                if i < len(paths): le.setText(paths[i])
        if hasattr(self, 'post_launch_app_line_edits'):
            paths = [config.post1_path, config.post2_path, config.post3_path]
            for i, le in enumerate(self.post_launch_app_line_edits):
                if i < len(paths): le.setText(paths[i])
                
        # Run-Wait Checkboxes
        if hasattr(self, 'pre_launch_run_wait_checkboxes'):
            for i, cb in enumerate(self.pre_launch_run_wait_checkboxes):
                cb.setChecked(config.run_wait_states.get(f'pre_{i+1}_run_wait', True))
        if hasattr(self, 'post_launch_run_wait_checkboxes'):
            for i, cb in enumerate(self.post_launch_run_wait_checkboxes):
                cb.setChecked(config.run_wait_states.get(f'post_{i+1}_run_wait', True))

    @pyqtSlot()
    def _sync_config_from_ui_and_save(self):
        """Updates the AppConfig model from the UI and saves it to disk."""
        # Sync Setup Tab widgets directly
        self._sync_config_from_setup_tab_ui(self.config)
        
        self.deployment_tab.sync_config_from_ui(self.config)
        
        # Apply visual settings immediately
        self._apply_visual_settings()
        
        config_manager.save_configuration(self.config)

    def _sync_config_from_setup_tab_ui(self, config):
        """Sync AppConfig from Setup Tab UI widgets."""
        # Support both list widget and combo box implementations
        if hasattr(self, 'source_dirs_list'):
            config.source_dirs = [self.source_dirs_list.item(i).text() for i in range(self.source_dirs_list.count())]
        elif hasattr(self, 'source_dirs_combo'):
            config.source_dirs = [self.source_dirs_combo.itemText(i) for i in range(self.source_dirs_combo.count())]
        if hasattr(self, 'excluded_dirs_list'):
            config.excluded_dirs = [self.excluded_dirs_list.item(i).text() for i in range(self.excluded_dirs_list.count())]
        elif hasattr(self, 'exclude_items_combo'):
            config.excluded_dirs = [self.exclude_items_combo.itemText(i) for i in range(self.exclude_items_combo.count())]
        if hasattr(self, 'other_managers_combo'): config.game_managers_present = self.other_managers_combo.currentText()
        if hasattr(self, 'exclude_manager_checkbox'): config.exclude_selected_manager_games = self.exclude_manager_checkbox.isChecked()
        if hasattr(self, 'logging_verbosity_combo'): config.logging_verbosity = self.logging_verbosity_combo.currentText()
        
        # Theme and font settings
        if hasattr(self, 'theme_combo'): config.app_theme = self.theme_combo.currentText()
        if hasattr(self, 'font_combo'): config.app_font = self.font_combo.currentText()
        if hasattr(self, 'font_size_spin'): config.font_size = self.font_size_spin.value()
        
        if hasattr(self, 'profiles_dir_edit'): config.profiles_dir = self.profiles_dir_edit.text()
        if hasattr(self, 'launchers_dir_edit'): config.launchers_dir = self.launchers_dir_edit.text()
        
        if hasattr(self, 'controller_mapper_app_line_edit'): config.controller_mapper_path = self.controller_mapper_app_line_edit.text()
        if hasattr(self, 'borderless_app_line_edit'): config.borderless_gaming_path = self.borderless_app_line_edit.text()
        if hasattr(self, 'multimonitor_app_line_edit'): config.multi_monitor_tool_path = self.multimonitor_app_line_edit.text()
        if hasattr(self, 'after_launch_app_line_edit'): config.just_after_launch_path = self.after_launch_app_line_edit.text()
        if hasattr(self, 'before_exit_app_line_edit'): config.just_before_exit_path = self.before_exit_app_line_edit.text()
        
        if hasattr(self, 'after_launch_run_wait_checkbox'): config.run_wait_states['just_after_launch_run_wait'] = self.after_launch_run_wait_checkbox.isChecked()
        if hasattr(self, 'before_exit_run_wait_checkbox'): config.run_wait_states['just_before_exit_run_wait'] = self.before_exit_run_wait_checkbox.isChecked()
        
        if hasattr(self, 'p1_profile_edit'): config.p1_profile_path = self.p1_profile_edit.text()
        if hasattr(self, 'p2_profile_edit'): config.p2_profile_path = self.p2_profile_edit.text()
        if hasattr(self, 'mediacenter_profile_edit'): config.mediacenter_profile_path = self.mediacenter_profile_edit.text()
        if hasattr(self, 'multimonitor_gaming_config_edit'): config.multimonitor_gaming_path = self.multimonitor_gaming_config_edit.text()
        if hasattr(self, 'multimonitor_media_config_edit'): config.multimonitor_media_path = self.multimonitor_media_config_edit.text()
        
        if hasattr(self, 'pre_launch_app_line_edits'):
            if len(self.pre_launch_app_line_edits) > 0: config.pre1_path = self.pre_launch_app_line_edits[0].text()
            if len(self.pre_launch_app_line_edits) > 1: config.pre2_path = self.pre_launch_app_line_edits[1].text()
            if len(self.pre_launch_app_line_edits) > 2: config.pre3_path = self.pre_launch_app_line_edits[2].text()
            
        if hasattr(self, 'post_launch_app_line_edits'):
            if len(self.post_launch_app_line_edits) > 0: config.post1_path = self.post_launch_app_line_edits[0].text()
            if len(self.post_launch_app_line_edits) > 1: config.post2_path = self.post_launch_app_line_edits[1].text()
            if len(self.post_launch_app_line_edits) > 2: config.post3_path = self.post_launch_app_line_edits[2].text()
            
        if hasattr(self, 'pre_launch_run_wait_checkboxes'):
            for i, cb in enumerate(self.pre_launch_run_wait_checkboxes):
                config.run_wait_states[f'pre_{i+1}_run_wait'] = cb.isChecked()
                
        if hasattr(self, 'post_launch_run_wait_checkboxes'):
            for i, cb in enumerate(self.post_launch_run_wait_checkboxes):
                config.run_wait_states[f'post_{i+1}_run_wait'] = cb.isChecked()
        
        # Sync CEN/LC modes for profile paths
        if hasattr(self, 'p1_cen_radio'):
            config.p1_profile_mode = "CEN" if self.p1_cen_radio.isChecked() else "LC"
        if hasattr(self, 'p2_cen_radio'):
            config.p2_profile_mode = "CEN" if self.p2_cen_radio.isChecked() else "LC"
        if hasattr(self, 'mediacenter_cen_radio'):
            config.mediacenter_profile_mode = "CEN" if self.mediacenter_cen_radio.isChecked() else "LC"
        if hasattr(self, 'multimonitor_gaming_cen_radio'):
            config.multimonitor_gaming_mode = "CEN" if self.multimonitor_gaming_cen_radio.isChecked() else "LC"
        if hasattr(self, 'multimonitor_media_cen_radio'):
            config.multimonitor_media_mode = "CEN" if self.multimonitor_media_cen_radio.isChecked() else "LC"

    def _add_to_list(self, list_widget, dialog_title, is_directory=False):
        """Add item to a QListWidget."""
        if is_directory:
            path = QFileDialog.getExistingDirectory(self, dialog_title)
        else:
            path, _ = QFileDialog.getOpenFileName(self, dialog_title)
        if path:
            list_widget.addItem(path)
            self._sync_config_from_ui_and_save()

    def _remove_from_list(self, list_widget):
        """Remove selected item from a QListWidget."""
        selected_items = list_widget.selectedItems()
        for item in selected_items:
            list_widget.takeItem(list_widget.row(item))
        self._sync_config_from_ui_and_save()

    def _on_appearance_changed(self):
        """Handle theme/font/size changes."""
        self._apply_visual_settings()
        self._sync_config_from_ui_and_save()

    def _apply_visual_settings(self):
        """Apply theme and font settings from configuration."""
        # Use getattr to safely get values, defaulting to System/10 if not in config yet
        theme = getattr(self.config, 'app_theme', 'System')
        font_size = getattr(self.config, 'font_size', 10)
        
        if theme == 'Dark':
            self._apply_dark_theme(font_size)
        else:
            self._apply_system_theme(font_size)

    def _apply_dark_theme(self, font_size):
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: #2b2b2b;
                color: #e0e0e0;
                font-family: "Segoe UI", Arial, sans-serif;
                font-size: {font_size}pt;
            }}
            QTabWidget::pane {{
                border: 1px solid #3d3d3d;
                background: #323232;
                border-radius: 4px;
            }}
            QTabBar::tab {{
                background: #2b2b2b;
                color: #a0a0a0;
                padding: 8px 20px;
                border: 1px solid #3d3d3d;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background: #323232;
                color: #ffffff;
                border-bottom: 1px solid #323232;
            }}
            QTabBar::tab:hover {{
                background: #3a3a3a;
                color: #ffffff;
            }}
            QLineEdit, QComboBox, QTableWidget {{
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                padding: 4px;
                border-radius: 3px;
            }}
            QPushButton, QToolButton {{
                background-color: #3a3a3a;
                color: #ffffff;
                border: 1px solid #555;
                padding: 6px 12px;
                border-radius: 3px;
            }}
            QPushButton:hover, QToolButton:hover {{
                background-color: #4a4a4a;
            }}
            QPushButton:pressed, QToolButton:pressed {{
                background-color: #2a2a2a;
            }}
            /* Specific styles for custom widgets */
            DragDropListWidget {{
                background-color: #1e1e1e;
                color: #e0e0e0;
                border: 1px solid #3d3d3d;
            }}
            DragDropListWidget::item:selected {{
                background-color: #0078d7;
                color: white;
            }}
            DragDropListWidget::item:hover {{
                background-color: #3a3a3a;
            }}
            AccordionSection QToolButton {{
                font-weight: bold;
                text-align: left;
            }}
        """)

    def _apply_system_theme(self, font_size):
        """Apply system theme with user-defined font size."""
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                font-family: "Segoe UI", Arial, sans-serif;
                font-size: {font_size}pt;
            }}
            /* Restore original DragDropListWidget styles */
            DragDropListWidget {{
                background-color: #E0E0E0;
                color: black;
                border: 1px solid #A0A0A0;
                border-radius: 4px;
            }}
            DragDropListWidget::item {{
                padding: 4px;
                border-bottom: 1px solid #C0C0C0;
            }}
            DragDropListWidget::item:selected {{
                background-color: #B0B0FF;
                color: black;
            }}
            DragDropListWidget::item:hover {{
                background-color: #D0D0FF;
            }}
            AccordionSection QToolButton {{
                font-weight: bold;
            }}
        """)

    def _add_to_list(self, list_widget, dialog_title, is_directory=False):
        """Add item to a QListWidget."""
        if is_directory:
            path = QFileDialog.getExistingDirectory(self, dialog_title)
        else:
            path, _ = QFileDialog.getOpenFileName(self, dialog_title)
        if path:
            list_widget.addItem(path)
            self._sync_config_from_ui_and_save()

    def _remove_from_list(self, list_widget):
        """Remove selected item from a QListWidget."""
        selected_items = list_widget.selectedItems()
        for item in selected_items:
            list_widget.takeItem(list_widget.row(item))
        self._sync_config_from_ui_and_save()

    def _on_appearance_changed(self):
        """Handle theme/font/size changes."""
        self._apply_visual_settings()
        self._sync_config_from_ui_and_save()

    def _reset_to_defaults(self):
        """Reset the application's configuration to shipped defaults."""
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(self, "Reset to Defaults",
                                     "This will reset all configuration to the application's default values. Continue?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        from Python.ui.config_manager import load_default_config
        success = load_default_config(self)
        if success:
            QMessageBox.information(self, "Defaults Loaded", "Default configuration has been loaded.")
            self._load_config()
        else:
            QMessageBox.warning(self, "Reset Failed", "Failed to load default configuration.")

    def on_create_button_clicked(self):
        """Handle the Create button click"""
        # Get the selected games data from the editor tab
        selected_games = self.editor_tab.get_selected_game_data()
        
        if not selected_games:
            QMessageBox.warning(self, "No Games Selected", "Please select at least one game to process.")
            return
        
        # Debug output to verify selected games
        print(f"Selected {len(selected_games)} games for processing")
        for i, game in enumerate(selected_games):
            print(f"Game {i+1}: {game.get('name_override', '')}")
        
        # Call create_all with the selected games
        result = self.creation_controller.create_all(selected_games)
        self.statusBar().showMessage(f"Creation process finished. Processed: {result['processed_count']}, Failed: {result['failed_count']}", 5000)

    def _backup_steam_cache_files(self):
        """Backup Steam cache files before processing"""
        # Get the cache file paths
        from Python.ui.steam_cache import STEAM_FILTERED_TXT, NORMALIZED_INDEX_CACHE
        filtered_cache_path = os.path.join(constants.APP_ROOT_DIR, STEAM_FILTERED_TXT)
        normalized_index_path = os.path.join(constants.APP_ROOT_DIR, NORMALIZED_INDEX_CACHE)
        
        # Backup filtered cache if it exists
        if os.path.exists(filtered_cache_path):
            backup_path = filtered_cache_path + ".old"
            try:
                # Remove old backup if it exists
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                
                # Create backup
                shutil.copy2(filtered_cache_path, backup_path)

            except Exception as e:
                pass
        
        # Backup normalized index if it exists
        if os.path.exists(normalized_index_path):
            backup_path = normalized_index_path + ".old"
            try:
                # Remove old backup if it exists
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                
                # Create backup
                shutil.copy2(normalized_index_path, backup_path)

            except Exception as e:
                pass
