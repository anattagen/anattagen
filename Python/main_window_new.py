from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QStatusBar, 
    QMessageBox, QMenu, QFileDialog, QTableWidgetItem, QCheckBox,
    QProgressDialog, QVBoxLayout, QHBoxLayout, QHeaderView, QMessageBox
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
from Python.ui.deployment_tab import DeploymentTab
from Python.ui.editor_tab_ui import populate_editor_tab
from Python.ui.steam_cache import SteamCacheManager
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
        
        found_games = index_games(
            source_dirs=self.config.source_dirs,
            exclude_exe_set=self.exclude_exe_set,
            folder_exclude_set=self.folder_exclude_set,
            demoted_set=self.demoted_set,
            folder_demoted_set=self.folder_demoted_set,
            release_groups_set=self.release_groups_set,
            enable_name_matching=self.config.enable_name_matching
        )
        
        self.main_window.editor_tab.populate_from_data(found_games)
        
        if found_games:
            data = self.main_window.editor_tab.get_all_game_data()
            save_index(self.main_window, constants.APP_ROOT_DIR, data)
        
        self.main_window.statusBar().showMessage(f"Indexed {len(found_games)} executables", 5000)

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

    def prompt_and_process_steam_json(self, file_path=None):
        """Prompt the user to select a Steam JSON file and process it."""
        from Python.ui.steam_processor import SteamProcessor
        
        # Check if steam_processor exists, if not create it
        if not hasattr(self, 'steam_processor'):
            self.steam_processor = SteamProcessor(self.main_window, self.steam_cache_manager)
        
        # Now that we're sure it exists, use it
        if file_path:
            self.steam_processor.process_steam_json_file(file_path)
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

        # Connect the setup tab's signal to our save logic
        self.setup_tab.config_changed.connect(self._sync_config_from_ui_and_save)
        
        # Connect the deployment tab's signals
        self.deployment_tab.config_changed.connect(self._sync_config_from_ui_and_save)
        self.deployment_tab.index_sources_requested.connect(self.data_manager.index_sources)
        self.deployment_tab.create_selected_requested.connect(self.on_create_button_clicked)
        self.deployment_tab.download_steam_json_requested.connect(self.steam_manager.download_steam_json)
        self.deployment_tab.delete_steam_json_requested.connect(self.steam_manager.delete_steam_json)
        self.deployment_tab.delete_steam_cache_requested.connect(self.steam_cache_manager.delete_cache_files)

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

    def _add_new_app_dialog(self, line_edit):
        """Handle the 'Add New...' option in app selection dropdowns"""
        # This is a placeholder for the actual implementation
        # It will be called when the user selects 'Add New...' in a dropdown
        pass
        
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
        # Delegate syncing the setup tab to its own class
        self.setup_tab.sync_ui_from_config(self.config)
        self.deployment_tab.sync_ui_from_config(self.config)

    @pyqtSlot()
    def _sync_config_from_ui_and_save(self):
        """Updates the AppConfig model from the UI and saves it to disk."""
        # Delegate syncing the setup tab to its own class
        self.setup_tab.sync_config_from_ui(self.config)
        self.deployment_tab.sync_config_from_ui(self.config)
        
        config_manager.save_configuration(self.config)

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
