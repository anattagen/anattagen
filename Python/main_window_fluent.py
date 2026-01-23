import os
import logging
import shutil
from qfluentwidgets import FluentWindow, NavigationItemPosition
from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QWidget

from Python.ui.deployment_tab import DeploymentTab
from Python.ui.setup_tab import SetupTab
from Python.ui.editor_tab import EditorTab
from Python.ui.steam_cache import SteamCacheManager, STEAM_FILTERED_TXT, NORMALIZED_INDEX_CACHE
from Python.models import AppConfig
from Python.managers.config_manager import ConfigManager
from Python.managers.data_manager import DataManager
from Python.managers.steam_manager import SteamManager
from Python import constants


class FluentMainWindow(FluentWindow):
    def __init__(self):
        import logging
        import shutil
        from qfluentwidgets import FluentWindow, NavigationItemPosition
        from PyQt6.QtCore import pyqtSlot
        from PyQt6.QtWidgets import QWidget

        from Python.ui.deployment_tab import DeploymentTab
        from Python.ui.setup_tab import SetupTab
        from Python.ui.editor_tab import EditorTab
        from Python.ui.steam_cache import SteamCacheManager, STEAM_FILTERED_TXT, NORMALIZED_INDEX_CACHE
        from Python.models import AppConfig
        from Python.managers.config_manager import ConfigManager
        from Python.managers.data_manager import DataManager
        from Python.managers.steam_manager import SteamManager
        from Python import constants
        from PyQt6.QtWidgets import (
            QApplication, QFileDialog, QProgressDialog
        )
        from PyQt6.QtCore import Qt, pyqtSlot
        from PyQt6.QtGui import QIcon, QCursor
        from qfluentwidgets import (
            FluentWindow, NavigationItemPosition, FluentIcon as FIF,
            TransparentToolButton, setTheme, Theme, isDarkTheme,
            MessageBox, RoundMenu
        )
        import os
        super().__init__()
        
        # Initialize managers
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()

        self.indexing_cancelled = False
        self.data_manager = DataManager(self.config, self)
        self.steam_cache_manager = SteamCacheManager(self)
        self.steam_manager = SteamManager(self.steam_cache_manager)
        
        self._setup_creation_controller()
        
        self.init_window()
        
        # Create interfaces
        self.setup_interface = SetupTab(self)
        self.deployment_interface = DeploymentTab(self)
        self.editor_interface = EditorTab(self)
        
        self.init_navigation()
        self._setup_theme_toggle()
        
        self._connect_signals()
        self.sync_ui_from_config()
        
        # Highlight unpopulated items
        self.deployment_interface.highlight_unpopulated_items(self)
        
        self.statusBar().showMessage("Ready")

    def init_window(self):
        self.setWindowTitle("Game Environment Manager")
        self.setWindowIcon(QIcon(constants.APP_ICON))
        self.resize(900, 700)
        
        # Center on screen
        desktop = QApplication.primaryScreen().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)

    def init_navigation(self):
        self.addSubInterface(self.setup_interface, FIF.SETTING, "Setup")
        self.addSubInterface(self.deployment_interface, FIF.ROCKET, "Deployment")
        self.addSubInterface(self.editor_interface, FIF.EDIT, "Editor")

    def _setup_theme_toggle(self):
        """Add a theme toggle button to the title bar."""
        self.theme_btn = TransparentToolButton(FIF.CONSTRUCT, self)
        self.theme_btn.setToolTip("Toggle Dark/Light Mode")
        self.theme_btn.clicked.connect(self._toggle_theme)
        
        # Insert into title bar layout before the system buttons
        # The layout usually contains [Icon, Title, Stretch, SystemButtons...]
        # Inserting at count() - 1 usually places it before the min/max/close buttons
        self.titleBar.layout().insertWidget(self.titleBar.layout().count(), self.theme_btn)
        self.titleBar.layout().insertSpacing(self.titleBar.layout().count(), 10)

    def _toggle_theme(self):
        """Switch between dark and light theme."""
        target = Theme.LIGHT if isDarkTheme() else Theme.DARK
        setTheme(target)

    def reset_configuration_to_defaults(self):
        """Handles the logic for resetting the app config to its default state."""
        self.config_manager.reset_to_defaults(self)
        MessageBox("Defaults Loaded", "Default configuration has been loaded and applied.", self).exec()

    def _load_steam_cache(self):
        """Load Steam cache from files"""
        self.steam_cache_manager.load_filtered_steam_cache()
        self.steam_cache_manager.load_normalized_steam_index()
        
    def _update_steam_json_cache(self):
        """Update the Steam JSON cache"""
        self.statusBar().showMessage("Updating Steam JSON cache...", 5000)
        
    def _locate_and_exclude_manager_config(self):
        """Locate and exclude games from other managers' configurations"""
        from Python.ui.steam_utils import locate_and_exclude_manager_config
        locate_and_exclude_manager_config(self)
        
    def _on_clear_listview(self):
        """Clear the editor table"""
        self.editor_interface.clear_table()
        self.statusBar().showMessage("List view cleared", 3000)

    def _connect_signals(self):
        """Connect signals from UI tabs and managers to slots."""
        # --- Manager Signals ---
        self.config_manager.status_updated.connect(self.statusBar().showMessage)
        self.data_manager.status_updated.connect(self.statusBar().showMessage)
        self.data_manager.status_updated.connect(self.deployment_interface.append_log_message)
        self.data_manager.index_data_loaded.connect(self.editor_interface.populate_from_data)

        self.steam_manager.status_updated.connect(self.statusBar().showMessage)
        self.steam_manager.status_updated.connect(self.deployment_interface.append_log_message)
        self.steam_manager.download_started.connect(self._disable_ui_for_long_process)
        self.steam_manager.download_finished.connect(self._enable_ui_after_long_process)
        self.steam_manager.processing_prompt_requested.connect(self._on_processing_prompt_requested)
        self.steam_manager.processing_started.connect(self._disable_ui_for_long_process)
        self.steam_manager.process_file_selection_requested.connect(self._on_process_file_selection_requested)
        self.steam_manager.processing_finished.connect(self._enable_ui_after_long_process)

        # --- UI Signals ---
        self.setup_interface.config_changed.connect(self._sync_config_from_ui_and_save)
        self.setup_interface.config_changed.connect(self.editor_interface.update_from_config)
        self.setup_interface.setting_changed.connect(lambda key: self.deployment_interface.update_overwrite_checkboxes(self.config, key))
        
        self.deployment_interface.config_changed.connect(self._sync_config_from_ui_and_save)
        self.deployment_interface.index_sources_requested.connect(self._on_index_sources_requested)
        self.deployment_interface.cancel_indexing_requested.connect(self._on_cancel_indexing_requested)
        self.deployment_interface.create_selected_requested.connect(self.on_create_button_clicked)
        self.deployment_interface.download_steam_json_requested.connect(self._on_download_steam_json_requested)
        self.deployment_interface.delete_steam_json_requested.connect(self._on_delete_steam_json_requested)
        self.deployment_interface.delete_steam_cache_requested.connect(self.steam_cache_manager.delete_cache_files)
        self.deployment_interface.process_steam_json_requested.connect(self._on_process_existing_json_requested)

        self.editor_interface.data_changed.connect(self.deployment_interface.update_create_button_count)
        self.editor_interface.save_index_requested.connect(self._on_save_index_requested)
        self.editor_interface.load_index_requested.connect(self._on_load_index_requested)
        self.editor_interface.delete_indexes_requested.connect(self._on_delete_indexes_requested)
        self.editor_interface.clear_view_requested.connect(self._on_clear_listview)

    @pyqtSlot()
    def _on_index_sources_requested(self):
        self.deployment_interface.set_indexing_state(True)
        self.indexing_cancelled = False
        self.data_manager.index_sources()
        self.deployment_interface.set_indexing_state(False)

    @pyqtSlot()
    def _on_cancel_indexing_requested(self):
        self.indexing_cancelled = True
        self.statusBar().showMessage("Cancelling indexing...", 3000)

    @pyqtSlot(int)
    def _on_download_steam_json_requested(self, version: int):
        if self.steam_manager.is_downloading:
            self.statusBar().showMessage("Download already in progress", 3000)
            return

        output_file = constants.STEAM_JSON_FILE
        if os.path.exists(output_file):
            w = MessageBox("Confirm Overwrite", f"The file 'steam.json' already exists. Are you sure you want to download and replace it?", self)
            if not w.exec():
                return
        
        self.steam_manager.download_steam_json(version)

    @pyqtSlot()
    def _on_delete_steam_json_requested(self):
        w = MessageBox("Delete Steam JSON", "Are you sure you want to delete steam.json?", self)
        if w.exec():
            self.steam_manager.delete_steam_json()

    @pyqtSlot()
    def _on_process_existing_json_requested(self):
        filtered_cache = os.path.join(constants.APP_ROOT_DIR, STEAM_FILTERED_TXT)
        normalized_cache = os.path.join(constants.APP_ROOT_DIR, NORMALIZED_INDEX_CACHE)
        
        if os.path.exists(filtered_cache) or os.path.exists(normalized_cache):
            w = MessageBox("Confirm Processing", "This will overwrite/delete existing Steam cache files. Are you sure you want to proceed?", self)
            if not w.exec():
                return
        
        self.steam_manager.process_existing_json()

    @pyqtSlot(str)
    def _on_processing_prompt_requested(self, file_path: str):
        w = MessageBox("Process Steam Data", "Steam data downloaded. Do you want to process it now? This may take some time.", self)
        if w.exec():
            self.steam_manager.prompt_and_process_steam_json(file_path)

    @pyqtSlot()
    def _on_process_file_selection_requested(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Steam JSON file", constants.APP_ROOT_DIR, "JSON Files (*.json)"
        )
        if file_path:
            self.steam_manager.prompt_and_process_steam_json(file_path)

    def _disable_ui_for_long_process(self):
        self.setup_interface.setEnabled(False)
        self.deployment_interface.setEnabled(False)
        self.editor_interface.setEnabled(False)

    def _enable_ui_after_long_process(self):
        self.setup_interface.setEnabled(True)
        self.deployment_interface.setEnabled(True)
        self.editor_interface.setEnabled(True)

    def _save_editor_table_to_index(self):
        file_path = os.path.join(constants.APP_ROOT_DIR, "current.index")
        data = self.editor_interface.get_all_game_data()
        self.data_manager.save_editor_table_to_index(data, file_path)

    @pyqtSlot()
    def _on_load_index_requested(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Index File", constants.APP_ROOT_DIR, "Index Files (*.index)"
        )
        if file_path:
            self.data_manager.load_index(file_path)

    @pyqtSlot()
    def _on_save_index_requested(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Index File", constants.APP_ROOT_DIR, "Index Files (*.index)"
        )
        if file_path:
            if not file_path.endswith(".index"):
                file_path += ".index"
            data = self.editor_interface.get_all_game_data()
            self.data_manager.save_editor_table_to_index(data, file_path)

    @pyqtSlot()
    def _on_delete_indexes_requested(self):
        w = MessageBox("Confirm Delete", "Are you sure you want to delete all index files?", self)
        if w.exec():
            self.data_manager.delete_indexes()

    def _setup_creation_controller(self):
        from Python.ui.creation.creation_controller import CreationController
        self.creation_controller = CreationController(self)

    @pyqtSlot(str)
    def _on_logging_verbosity_changed(self, level_text):
        level_map = {
            "None": logging.CRITICAL + 1,
            "Low": logging.WARNING,
            "Medium": logging.INFO,
            "High": logging.DEBUG,
            "Debug": logging.DEBUG
        }
        log_level = level_map.get(level_text, logging.INFO)
        logging.getLogger().setLevel(log_level)
        logging.warning(f"Logging level changed to: {level_text} ({log_level})")
        self.statusBar().showMessage(f"Logging level set to {level_text}", 3000)
        self.config.logging_verbosity = level_text
        self.config_manager.save_config(self.config)
        
    def sync_ui_from_config(self):
        self.setup_interface.sync_ui_from_config(self.config)
        self.deployment_interface.sync_ui_from_config(self.config)

    @pyqtSlot()
    def _sync_config_from_ui_and_save(self):
        self.setup_interface.sync_config_from_ui(self.config)
        self.deployment_interface.sync_config_from_ui(self.config)
        self.config_manager.save_config(self.config)

    def on_create_button_clicked(self):
        all_games = self.editor_interface.get_all_game_data()
        games_to_process = [g for g in all_games if g.get('create')]
        
        if not games_to_process:
            MessageBox("No Games to Create", "Please mark at least one game with 'Create' in the Editor tab.", self).exec()
            return
        
        missing_items = self.creation_controller.validate_prerequisites(games_to_process)
        if missing_items:
            msg = "The following referenced files are missing:\n\n" + "\n".join([f"- {item}" for item in missing_items[:10]])
            if len(missing_items) > 10: msg += f"\n... and {len(missing_items) - 10} more."
            msg += "\n\nDo you want to proceed anyway?"
            w = MessageBox("Missing Files Detected", msg, self)
            if not w.exec():
                return

        create_count = len(games_to_process)
        msg_text = f"<h3>Creation Summary</h3>Items to be created: <b>{create_count}</b><br><br>Proceed with creation?"
        
        w = MessageBox("Confirm Creation", msg_text, self)
        if not w.exec():
            return

        progress = QProgressDialog("Creating launchers...", "Cancel", 0, create_count, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        
        def update_progress(current, _, game_name):
            if progress.wasCanceled(): return False
            self.deployment_interface.append_log_message(f"Creating launcher for: {game_name}")
            progress.setValue(current)
            progress.setLabelText(f"Creating launcher for: {game_name}")
            QApplication.processEvents()
            return True

        result = self.creation_controller.create_all(games_to_process, progress_callback=update_progress)
        progress.setValue(create_count)
        
        status_msg = f"Creation {'cancelled' if progress.wasCanceled() else 'finished'}. Processed: {result['processed_count']}, Failed: {result['failed_count']}"
        self.statusBar().showMessage(status_msg, 5000)
        self.deployment_interface.append_log_message(status_msg)