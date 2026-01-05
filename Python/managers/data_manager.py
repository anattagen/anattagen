import os
import json
import logging
from PyQt6.QtCore import QObject, pyqtSignal, Qt
from PyQt6.QtWidgets import QProgressDialog

from .. import constants
from ..models import AppConfig
from ..ui.game_indexer import index_games


class DataManager(QObject):
    """Manages loading, saving, and indexing of game data."""
    status_updated = pyqtSignal(str, int)
    index_data_loaded = pyqtSignal(list)

    def __init__(self, config: AppConfig, main_window):
        super().__init__()
        self.config = config
        self.main_window = main_window

    def _load_set_file(self, filename):
        """Loads a .set file into a set of strings from the assets directory."""
        result = set()
        file_path = os.path.join(constants.ASSETS_DIR, filename)
        if not os.path.exists(file_path):
            logging.warning(f"Set file not found: {file_path}")
            return result
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                for line in f:
                    line = line.strip().lower()
                    if line and not line.startswith('#'):
                        result.add(line)
        except Exception as e:
            logging.error(f"Failed to load set file {filename}: {e}")
        return result

    def index_sources(self):
        """
        Scans source directories for games and emits the data for the UI.
        """
        self.status_updated.emit("Indexing game sources...", 0)
        logging.info("Starting to index game sources.")
        
        # Reset the cancellation flag
        self.main_window.indexing_cancelled = False
        
        # Initialize a set to track processed paths for this session
        self.main_window.processed_paths = set()

        # Create and manage the progress dialog
        progress = QProgressDialog("Indexing games...", "Cancel", 0, 0, self.main_window)
        progress.setWindowTitle("Indexing Games")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.canceled.connect(lambda: setattr(self.main_window, 'indexing_cancelled', True))
        progress.show()

        try:
            # Load necessary data sets for the indexer
            self.main_window.exclude_exe_set = self._load_set_file("exclude_exe.set")
            self.main_window.folder_exclude_set = self._load_set_file("folder_exclude.set")
            self.main_window.demoted_set = self._load_set_file("demoted.set")
            self.main_window.folder_demoted_set = self._load_set_file("folder_demoted.set")
            self.main_window.release_groups_set = self._load_set_file("release_groups.set")

            # Call the refactored, UI-agnostic indexer
            found_games = index_games(self.main_window)

            if self.main_window.indexing_cancelled:
                logging.info("Indexing was cancelled by the user.")
                self.status_updated.emit("Indexing cancelled.", 3000)
                # Emit empty list to clear the view if cancelled
                self.index_data_loaded.emit([])
            else:
                logging.info(f"Indexing complete. Found {len(found_games)} games.")
                self.status_updated.emit(f"Found {len(found_games)} games.", 3000)
                self.index_data_loaded.emit(found_games)

                # Automatically save the index file
                if found_games:
                    index_file_path = os.path.join(constants.APP_ROOT_DIR, "current.index")
                    self.save_editor_table_to_index(found_games, index_file_path)

        except Exception as e:
            logging.error(f"Error during indexing: {e}", exc_info=True)
            self.status_updated.emit(f"Error during indexing: {e}", 5000)
        finally:
            # Ensure the progress dialog is closed
            progress.close()

    def load_index(self, file_path):
        """Loads game data from a .index file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                games_data = json.load(f)
            self.index_data_loaded.emit(games_data)
            self.status_updated.emit(f"Loaded {len(games_data)} games from {os.path.basename(file_path)}", 3000)
        except Exception as e:
            logging.error(f"Failed to load index file {file_path}: {e}")
            self.status_updated.emit(f"Failed to load index file: {e}", 5000)

    def save_editor_table_to_index(self, data, file_path):
        """Saves the current editor table data to a .index file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            self.status_updated.emit(f"Saved {len(data)} games to {os.path.basename(file_path)}", 3000)
        except Exception as e:
            logging.error(f"Failed to save index file {file_path}: {e}")
            self.status_updated.emit(f"Failed to save index file: {e}", 5000)

    def delete_indexes(self):
        """Deletes all .index files in the application root directory."""
        deleted_count = 0
        try:
            for item in os.listdir(constants.APP_ROOT_DIR):
                if item.endswith(".index"):
                    file_path = os.path.join(constants.APP_ROOT_DIR, item)
                    try:
                        os.remove(file_path)
                        deleted_count += 1
                        logging.info(f"Deleted index file: {file_path}")
                    except OSError as e:
                        logging.error(f"Error deleting index file {file_path}: {e}")
            if deleted_count > 0:
                self.status_updated.emit(f"Deleted {deleted_count} index files.", 3000)
                self.index_data_loaded.emit([]) # Clear the editor view
            else:
                self.status_updated.emit("No index files found to delete.", 3000)
        except Exception as e:
            logging.error(f"Error accessing application root directory: {e}")
            self.status_updated.emit("Error deleting index files.", 5000)