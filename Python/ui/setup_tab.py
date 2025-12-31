import logging
import os
import sys
import configparser
import requests
import zipfile
import shutil
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QLabel, QFormLayout, QPushButton,
    QComboBox, QHBoxLayout, QCheckBox, QTabWidget,
    QFileDialog, QApplication, QStyleFactory, QSpinBox, QMessageBox, QProgressBar,
    QDialog, QDialogButtonBox, QLineEdit
)
from PyQt6.QtGui import QFontDatabase, QFont, QPalette, QColor
from PyQt6.QtCore import pyqtSignal, Qt, QThread, pyqtSlot
from Python.models import AppConfig
from Python.ui.widgets import DragDropListWidget, PathConfigRow
from Python.ui.accordion import AccordionSection
from Python import constants

class DownloadThread(QThread):
    """Thread for downloading and extracting tools."""
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool, str, str) # success, message, result_path

    def __init__(self, url, extract_dir, exe_name):
        super().__init__()
        self.url = url
        self.extract_dir = extract_dir
        self.exe_name = exe_name

    def run(self):
        try:
            # Create extract directory
            os.makedirs(self.extract_dir, exist_ok=True)
            
            # Determine filename from URL
            filename = self.url.split('/')[-1]
            save_path = os.path.join(self.extract_dir, filename)
            
            # Download
            response = requests.get(self.url, stream=True)
            response.raise_for_status()
            total_length = response.headers.get('content-length')

            with open(save_path, 'wb') as f:
                if total_length is None: # no content length header
                    f.write(response.content)
                else:
                    dl = 0
                    total_length = int(total_length)
                    for data in response.iter_content(chunk_size=4096):
                        dl += len(data)
                        f.write(data)
                        self.progress.emit(int(100 * dl / total_length))
            
            # Extract if it's a zip
            if filename.lower().endswith('.zip'):
                with zipfile.ZipFile(save_path, 'r') as zip_ref:
                    zip_ref.extractall(self.extract_dir)
                os.remove(save_path) # Clean up zip
            elif filename.lower().endswith('.7z'):
                # Basic handling: just leave the 7z if we can't extract it easily without extra libs
                # Or assume user handles it. For now, we just leave it.
                pass
                
            # Construct result path
            result_path = os.path.join(self.extract_dir, self.exe_name)
            if not os.path.exists(result_path):
                # Try to find it recursively if not found at root
                for root, dirs, files in os.walk(self.extract_dir):
                    if self.exe_name in files:
                        result_path = os.path.join(root, self.exe_name)
                        break
            
            self.finished.emit(True, "Download complete", result_path)
            
        except Exception as e:
            self.finished.emit(False, str(e), "")

class SetupTab(QWidget):
    """A QWidget that encapsulates all UI and logic for the Setup tab."""
    
    config_changed = pyqtSignal()
    
    PATH_ATTRIBUTES = [
        "profiles_dir", "launchers_dir", "launcher_executable", "controller_mapper_path", 
        "borderless_gaming_path", "multi_monitor_tool_path",
        "p1_profile_path", "p2_profile_path", "mediacenter_profile_path",
        "multimonitor_gaming_path", "multimonitor_media_path",
        "pre1_path", "pre2_path", "pre3_path",
        "just_after_launch_path", "just_before_exit_path",
        "post1_path", "post2_path", "post3_path"
    ]

    def __init__(self, parent=None): # parent is main_window
        super().__init__(parent)
        self.main_window = parent
        self.path_rows = {}
        self.repos = self._parse_repos_set()
        self.download_thread = None
        self._setup_ui()

    def _add_path_row(self, layout, label_text, config_key, row_widget):
        """Helper to add a row with a context-menu-capable label."""
        label = QLabel(label_text)
        label.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        label.customContextMenuRequested.connect(lambda pos: self._show_options_args_dialog(pos, config_key, label_text))
        layout.addRow(label, row_widget)

    def _setup_ui(self):
        """Create and arrange all widgets for the Setup tab."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # --- Section 1: Sources & Indexing ---
        source_config_widget = QWidget()
        source_config_layout = QFormLayout(source_config_widget)
        source_config_layout.setSpacing(10)

        # Sources
        self.source_dirs_list = DragDropListWidget()
        self.source_dirs_list.setMaximumHeight(100)
        add_source_button = QPushButton("Add...")
        remove_source_button = QPushButton("Remove")
        source_buttons_layout = QVBoxLayout()
        source_buttons_layout.addWidget(add_source_button)
        source_buttons_layout.addWidget(remove_source_button)
        source_buttons_layout.addStretch()
        source_dirs_layout = QHBoxLayout()
        source_dirs_layout.addWidget(self.source_dirs_list, 1)
        source_dirs_layout.addLayout(source_buttons_layout)
        source_config_layout.addRow("Source Directories:", source_dirs_layout)
        self.add_source_dir_button = add_source_button
        self.remove_source_dir_button = remove_source_button

        # Excluded Items
        self.excluded_dirs_list = DragDropListWidget()
        self.excluded_dirs_list.setMaximumHeight(100)
        add_excluded_button = QPushButton("Add...")
        remove_excluded_button = QPushButton("Remove")
        excluded_buttons_layout = QVBoxLayout()
        excluded_buttons_layout.addWidget(add_excluded_button)
        excluded_buttons_layout.addWidget(remove_excluded_button)
        excluded_buttons_layout.addStretch()
        excluded_layout = QHBoxLayout()
        excluded_layout.addWidget(self.excluded_dirs_list, 1)
        excluded_layout.addLayout(excluded_buttons_layout)
        source_config_layout.addRow("Excluded Directories:", excluded_layout)
        self.add_excluded_dir_button = add_excluded_button
        self.remove_excluded_dir_button = remove_excluded_button

        # Game managers
        self.other_managers_combo = QComboBox()
        self.other_managers_combo.addItems(["None", "Steam", "Epic", "GOG", "Origin", "Ubisoft Connect", "Battle.net", "Xbox"])
        self.exclude_manager_checkbox = QCheckBox("Exclude Selected Manager's Games")
        game_managers_layout = QHBoxLayout()
        game_managers_layout.addWidget(self.other_managers_combo)
        game_managers_layout.addWidget(self.exclude_manager_checkbox)
        game_managers_layout.addStretch(1)
        source_config_layout.addRow("Game Managers Present:", game_managers_layout)

        source_config_section = AccordionSection("Sources & Indexing", source_config_widget)

        # --- Section 2: Paths & Profiles ---
        paths_widget = QWidget()
        paths_layout = QVBoxLayout(paths_widget)
        paths_layout.setContentsMargins(0,0,0,0)
        paths_tabs = QTabWidget()
        paths_layout.addWidget(paths_tabs)

        # Core Paths Tab
        # Prepare repo items for generic lists (All except GLOBAL)
        all_tools = {}
        for section, items in self.repos.items():
            if section != "GLOBAL":
                all_tools.update(items)

        core_paths_widget = QWidget()
        core_paths_layout = QFormLayout(core_paths_widget)
        self.path_rows["profiles_dir"] = PathConfigRow("profiles_dir", is_directory=True, add_enabled=True, add_cen_lc=True)
        self.path_rows["profiles_dir"].enabled_cb.setToolTip("Create Profile Folders")
        core_paths_layout.addRow("Profiles Directory:", self.path_rows["profiles_dir"]) # No options/args for dirs
        self.path_rows["launchers_dir"] = PathConfigRow("launchers_dir", is_directory=True, add_enabled=True, add_cen_lc=True)
        self.path_rows["launchers_dir"].enabled_cb.setToolTip("Create Launcher")
        core_paths_layout.addRow("Launchers Directory:", self.path_rows["launchers_dir"]) # No options/args for dirs
        self.path_rows["launcher_executable"] = PathConfigRow("launcher_executable", is_directory=False, add_enabled=False, add_cen_lc=False)
        self.path_rows["launcher_executable"].line_edit.setPlaceholderText(constants.LAUNCHER_EXECUTABLE)
        core_paths_layout.addRow("Launcher Executable:", self.path_rows["launcher_executable"]) # Internal
        paths_tabs.addTab(core_paths_widget, "Core")

        # Application Paths Tab
        app_paths_widget = QWidget()
        app_paths_layout = QFormLayout(app_paths_widget)
        self.path_rows["controller_mapper_path"] = PathConfigRow("controller_mapper_path", add_run_wait=True, repo_items=self.repos.get("MAPPERS"))
        self.path_rows["controller_mapper_path"].enabled_cb.setToolTip("Enable Controller Mapper")
        self._add_path_row(app_paths_layout, "Controller Mapper:", "controller_mapper_path", self.path_rows["controller_mapper_path"])
        self.path_rows["borderless_gaming_path"] = PathConfigRow("borderless_gaming_path", add_run_wait=True, repo_items=self.repos.get("WINDOWING"))
        self.path_rows["borderless_gaming_path"].enabled_cb.setToolTip("Enable Borderless Windowing")
        self._add_path_row(app_paths_layout, "Borderless Windowing:", "borderless_gaming_path", self.path_rows["borderless_gaming_path"])
        self.path_rows["multi_monitor_tool_path"] = PathConfigRow("multi_monitor_tool_path", add_run_wait=True, repo_items=self.repos.get("DISPLAY"))
        self.path_rows["multi_monitor_tool_path"].enabled_cb.setToolTip("Enable Multi-Monitor Tool")
        self._add_path_row(app_paths_layout, "Multi-Monitor App:", "multi_monitor_tool_path", self.path_rows["multi_monitor_tool_path"])
        self.path_rows["just_after_launch_path"] = PathConfigRow("just_after_launch_path", add_run_wait=True, repo_items=all_tools)
        self.path_rows["just_after_launch_path"].enabled_cb.setToolTip("Enable Just After Launch App")
        self._add_path_row(app_paths_layout, "Just After Launch:", "just_after_launch_path", self.path_rows["just_after_launch_path"])
        self.path_rows["just_before_exit_path"] = PathConfigRow("just_before_exit_path", add_run_wait=True, repo_items=all_tools)
        self.path_rows["just_before_exit_path"].enabled_cb.setToolTip("Enable Just Before Exit App")
        self._add_path_row(app_paths_layout, "Just Before Exit:", "just_before_exit_path", self.path_rows["just_before_exit_path"])
        paths_tabs.addTab(app_paths_widget, "Applications")

        # Profile Paths Tab
        profile_paths_widget = QWidget()
        profile_paths_layout = QFormLayout(profile_paths_widget)
        self.path_rows["p1_profile_path"] = PathConfigRow("p1_profile_path", add_enabled=False)
        profile_paths_layout.addRow("Player 1 Profile:", self.path_rows["p1_profile_path"])
        self.path_rows["p2_profile_path"] = PathConfigRow("p2_profile_path", add_enabled=False)
        profile_paths_layout.addRow("Player 2 Profile:", self.path_rows["p2_profile_path"])
        self.path_rows["mediacenter_profile_path"] = PathConfigRow("mediacenter_profile_path", add_enabled=False)
        profile_paths_layout.addRow("Media Center Profile:", self.path_rows["mediacenter_profile_path"])
        self.path_rows["multimonitor_gaming_path"] = PathConfigRow("multimonitor_gaming_path", add_enabled=False)
        profile_paths_layout.addRow("MM Gaming Config:", self.path_rows["multimonitor_gaming_path"])
        self.path_rows["multimonitor_media_path"] = PathConfigRow("multimonitor_media_path", add_enabled=False)
        profile_paths_layout.addRow("MM Media/Desktop Config:", self.path_rows["multimonitor_media_path"])
        paths_tabs.addTab(profile_paths_widget, "Profiles")

        # Script Paths Tab
        script_paths_widget = QWidget()
        script_paths_layout = QFormLayout(script_paths_widget)
        for i in range(1, 4):
            key = f"pre{i}_path"
            self.path_rows[key] = PathConfigRow(key, add_run_wait=True, repo_items=all_tools)
            self.path_rows[key].enabled_cb.setToolTip(f"Enable Pre-Launch App {i}")
            self._add_path_row(script_paths_layout, f"Pre-Launch App {i}:", key, self.path_rows[key])
        for i in range(1, 4):
            key = f"post{i}_path"
            self.path_rows[key] = PathConfigRow(key, add_run_wait=True, repo_items=all_tools)
            self.path_rows[key].enabled_cb.setToolTip(f"Enable Post-Launch App {i}")
            self._add_path_row(script_paths_layout, f"Post-Launch App {i}:", key, self.path_rows[key])
        paths_tabs.addTab(script_paths_widget, "Scripts")
        
        paths_section = AccordionSection("Paths & Profiles", paths_widget)

        # --- Section 3: Execution Sequence ---
        sequences_widget = QWidget()
        sequences_layout = QHBoxLayout(sequences_widget)

        # Launch Sequence
        launch_sequence_group = QGroupBox("Launch Order")
        launch_sequence_layout = QVBoxLayout(launch_sequence_group)
        self.launch_sequence_list = DragDropListWidget()
        self.reset_launch_btn = QPushButton("Reset")
        launch_sequence_layout.addWidget(self.launch_sequence_list)
        launch_sequence_layout.addWidget(self.reset_launch_btn)
        sequences_layout.addWidget(launch_sequence_group)

        # Exit Sequence
        exit_sequence_group = QGroupBox("Exit Order")
        exit_sequence_layout = QVBoxLayout(exit_sequence_group)
        self.exit_sequence_list = DragDropListWidget()
        self.reset_exit_btn = QPushButton("Reset")
        exit_sequence_layout.addWidget(self.exit_sequence_list)
        exit_sequence_layout.addWidget(self.reset_exit_btn)
        sequences_layout.addWidget(exit_sequence_group)
        sequences_section = AccordionSection("Execution Sequences", sequences_widget)

        # --- Section 4: Appearance & Behavior ---
        appearance_widget = QWidget()
        appearance_layout = QFormLayout(appearance_widget)
        # Logging Verbosity
        self.logging_verbosity_combo = QComboBox()
        self.logging_verbosity_combo.addItems(["None", "Low", "Medium", "High", "Debug"])
        appearance_layout.addRow("Logging Verbosity:", self.logging_verbosity_combo)
        # Font
        font_layout = QHBoxLayout()
        self.font_combo = QComboBox()
        self.font_combo.addItem("System")
        custom_fonts = self._load_and_get_custom_fonts()
        self.font_combo.addItems(custom_fonts)
        font_layout.addWidget(self.font_combo)
        font_layout.addWidget(QLabel("Size:"))
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(10)
        font_layout.addWidget(self.font_size_spin)
        appearance_layout.addRow("Font:", font_layout)
        # Theme
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["System", "Fusion Dark", "Fusion Light"])
        available_styles = [s.lower() for s in QStyleFactory.keys()]
        if "windows" in available_styles:
            self.theme_combo.addItem("Windows")
        if "windowsvista" in available_styles:
            self.theme_combo.addItem("WindowsVista")
        if "material" in available_styles:
            self.theme_combo.addItems(["Material Light", "Material Dark"])
        appearance_layout.addRow("Theme:", self.theme_combo)
        # Restart Button
        self.restart_btn = QPushButton("Reset to Defaults")
        self.restart_btn.setToolTip("Reset all application configuration to defaults")
        appearance_layout.addRow(self.restart_btn)
        appearance_section = AccordionSection("Appearance & Behavior", appearance_widget)

        # Progress Bar for downloads
        self.download_progress = QProgressBar()
        self.download_progress.setVisible(False)
        main_layout.addWidget(self.download_progress)

        main_layout.addWidget(source_config_section)
        main_layout.addWidget(paths_section)
        main_layout.addWidget(sequences_section)
        main_layout.addWidget(appearance_section)
        main_layout.addStretch()
        self._connect_signals()

    def _show_options_args_dialog(self, pos, config_key, label_text):
        """Show a modal dialog to edit options and arguments for the selected app."""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Options & Arguments - {label_text.strip(':')}")
        layout = QFormLayout(dialog)
        
        options_edit = QLineEdit()
        options_edit.setText(getattr(self.main_window.config, f"{config_key}_options", ""))
        layout.addRow("Options:", options_edit)
        
        args_edit = QLineEdit()
        args_edit.setText(getattr(self.main_window.config, f"{config_key}_arguments", ""))
        layout.addRow("Arguments:", args_edit)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        if dialog.exec():
            setattr(self.main_window.config, f"{config_key}_options", options_edit.text())
            setattr(self.main_window.config, f"{config_key}_arguments", args_edit.text())
            self.config_changed.emit()

    def _connect_signals(self):
        self.add_source_dir_button.clicked.connect(self._add_source_dir)
        self.remove_source_dir_button.clicked.connect(self._remove_source_dir)
        self.add_excluded_dir_button.clicked.connect(self._add_excluded_dir)
        self.remove_excluded_dir_button.clicked.connect(self._remove_excluded_dir)
        self.reset_launch_btn.clicked.connect(self._reset_launch_sequence)
        self.reset_exit_btn.clicked.connect(self._reset_exit_sequence)

        self.source_dirs_list.model().rowsMoved.connect(self.config_changed.emit)
        self.source_dirs_list.model().rowsInserted.connect(self.config_changed.emit)
        self.source_dirs_list.model().rowsRemoved.connect(self.config_changed.emit)
        self.excluded_dirs_list.model().rowsMoved.connect(self.config_changed.emit)
        self.excluded_dirs_list.model().rowsInserted.connect(lambda: self.config_changed.emit())
        self.excluded_dirs_list.model().rowsRemoved.connect(self.config_changed.emit)
        # Path rows
        for row in self.path_rows.values():
            row.valueChanged.connect(self.config_changed.emit)
            row.downloadRequested.connect(self._on_download_requested)

        # Sequences
        self.launch_sequence_list.model().layoutChanged.connect(self.config_changed.emit)
        self.exit_sequence_list.model().layoutChanged.connect(self.config_changed.emit)

        # Logging
        self.logging_verbosity_combo.currentTextChanged.connect(self.main_window._on_logging_verbosity_changed)
        
        # Appearance
        self.font_combo.currentTextChanged.connect(self._on_appearance_changed)
        self.font_size_spin.valueChanged.connect(self._on_appearance_changed)
        self.theme_combo.currentTextChanged.connect(self._on_appearance_changed)
        self.restart_btn.clicked.connect(self._reset_to_defaults)

    def _parse_repos_set(self):
        """Parses the repos.set file and returns a dictionary of tools."""
        repos = {}
        if not os.path.exists(constants.REPOS_SET):
            return repos

        config = configparser.ConfigParser()
        config.read(constants.REPOS_SET)

        global_vars = {}
        if "GLOBAL" in config:
            global_vars = dict(config["GLOBAL"])
            # Pre-resolve common variables
            global_vars["app_directory"] = constants.APP_ROOT_DIR

        for section in config.sections():
            repos[section] = {}
            for key, value in config[section].items():
                if section == "GLOBAL": continue
                
                # Basic variable substitution
                val = value
                for var_name, var_val in global_vars.items():
                    val = val.replace(f"${var_name.upper()}", var_val)
                    val = val.replace(f"${var_name}", var_val)
                
                # Item specific substitution
                val = val.replace("$ITEMNAME", key)
                
                parts = val.split('|')
                if len(parts) >= 3:
                    repos[section][key] = {
                        'url': parts[0],
                        'extract_dir': parts[1],
                        'exe_name': parts[2]
                    }
        return repos

    def _on_download_requested(self, tool_name, tool_data):
        """Initiates the download of a tool."""
        if self.download_thread and self.download_thread.isRunning():
            QMessageBox.warning(self, "Download in Progress", "Please wait for the current download to finish.")
            return

        self.download_progress.setValue(0)
        self.download_progress.setVisible(True)
        self.download_progress.setFormat(f"Downloading {tool_name}... %p%")

        self.download_thread = DownloadThread(tool_data['url'], tool_data['extract_dir'], tool_data['exe_name'])
        self.download_thread.progress.connect(self.download_progress.setValue)
        self.download_thread.finished.connect(lambda success, msg, path: self._on_download_finished(success, msg, path, self.sender()))
        self.download_thread.start()

    def _on_download_finished(self, success, message, result_path, sender_row):
        self.download_progress.setVisible(False)
        if success:
            # Find which row sent the request (this is tricky with async, so we might need to store the active row)
            # For simplicity, we can iterate rows to find which one matches the tool or just update the one that triggered it if we passed it.
            # Actually, the sender() in _on_download_requested is the PathConfigRow.
            # We need to pass that reference to the finished callback.
            # I updated the lambda above to pass self.sender() but self.sender() in _on_download_requested is the row.
            # However, in the lambda for finished, self.sender() is the thread.
            # So we need to capture the row in _on_download_requested.
            pass # Logic handled by closure in _on_download_requested if implemented correctly, 
                 # but here I need to update the UI.
            
            # Since I can't easily pass the row instance through the thread without modifying the thread class or using a closure
            # Let's assume the user wants to set the path for the row they clicked.
            # A robust way is to store self.active_download_row in _on_download_requested.
            if hasattr(self, 'active_download_row') and self.active_download_row:
                self.active_download_row.line_edit.setText(result_path)
                self.active_download_row = None
            
            QMessageBox.information(self, "Download Complete", f"Successfully downloaded to:\n{result_path}")
        else:
            QMessageBox.critical(self, "Download Failed", f"Error: {message}")
            self.active_download_row = None

    # Update _on_download_requested to store the row
    def _on_download_requested(self, tool_name, tool_data):
        if self.download_thread and self.download_thread.isRunning():
            QMessageBox.warning(self, "Download in Progress", "Please wait for the current download to finish.")
            return

        self.active_download_row = self.sender() # Store the row that requested the download
        
        self.download_progress.setValue(0)
        self.download_progress.setVisible(True)
        self.download_progress.setFormat(f"Downloading {tool_name}... %p%")

        self.download_thread = DownloadThread(tool_data['url'], tool_data['extract_dir'], tool_data['exe_name'])
        self.download_thread.progress.connect(self.download_progress.setValue)
        self.download_thread.finished.connect(self._on_download_finished_slot)
        self.download_thread.start()

    def _on_download_finished_slot(self, success, message, result_path):
        self.download_progress.setVisible(False)
        if success:
            if hasattr(self, 'active_download_row') and self.active_download_row:
                self.active_download_row.line_edit.setText(result_path)
            QMessageBox.information(self, "Download Complete", f"Successfully downloaded to:\n{result_path}")
        else:
            QMessageBox.critical(self, "Download Failed", f"Error: {message}")
        self.active_download_row = None

    def _load_and_get_custom_fonts(self):
        """Load fonts from the 'site' directory and return their family names."""
        custom_fonts = []
        site_path = os.path.join(constants.APP_ROOT_DIR, "site")
        if os.path.exists(site_path):
            for f in os.listdir(site_path):
                if f.lower().endswith((".ttf", ".otf")):
                    font_path = os.path.join(site_path, f)
                    font_id = QFontDatabase.addApplicationFont(font_path)
                    if font_id != -1:
                        families = QFontDatabase.applicationFontFamilies(font_id)
                        if families:
                            custom_fonts.append(families[0])
        return sorted(list(set(custom_fonts)))

    def _reset_to_defaults(self):
        """Reset the application's configuration to the shipped defaults."""
        reply = QMessageBox.question(self, "Reset to Defaults",
                                     "This will reset all configuration to the application's default values. Continue?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Call the main window's method to handle the reset logic
        if hasattr(self.main_window, 'reset_configuration_to_defaults'):
            self.main_window.reset_configuration_to_defaults()

    def _add_source_dir(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Source Directory")
        if directory:
            self.source_dirs_list.addItem(directory)

    def _remove_source_dir(self):
        selected_items = self.source_dirs_list.selectedItems()
        if not selected_items:
            return
        for item in selected_items:
            self.source_dirs_list.takeItem(self.source_dirs_list.row(item))

    def _add_excluded_dir(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory to Exclude")
        if directory:
            self.excluded_dirs_list.addItem(directory)

    def _remove_excluded_dir(self):
        selected_items = self.excluded_dirs_list.selectedItems()
        if not selected_items:
            return
        for item in selected_items:
            self.excluded_dirs_list.takeItem(self.excluded_dirs_list.row(item))

    def _reset_launch_sequence(self):
        self.launch_sequence_list.clear()
        self.launch_sequence_list.addItems(["Controller-Mapper", "Monitor-Config", "No-TB", "Pre1", "Pre2", "Pre3", "Borderless"])
        self.config_changed.emit()

    def _reset_exit_sequence(self):
        self.exit_sequence_list.clear()
        self.exit_sequence_list.addItems(["Post1", "Post2", "Post3", "Monitor-Config", "Taskbar", "Controller-Mapper"])
        self.config_changed.emit()

    def _on_appearance_changed(self):
        self.config_changed.emit()
        self._apply_visual_settings()

    def _create_dark_palette(self):
        """Creates a QPalette for a dark theme."""
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        
        dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(127, 127, 127))
        dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(127, 127, 127))
        dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(127, 127, 127))
        return dark_palette

    def _apply_visual_settings(self):
        """Apply theme and font settings from configuration."""
        app = QApplication.instance()
        if not app:
            return

        theme = self.theme_combo.currentText()
        font_name = self.font_combo.currentText() or "System"
        font_size = self.font_size_spin.value()

        # 1. Set Font
        font = QFont()
        if font_name != "System":
            font.setFamily(font_name)
        font.setPointSize(font_size)
        app.setFont(font)

        # 2. Set Theme/Style
        app.setStyleSheet("") # Clear any previous stylesheet

        if theme == 'System':
            # Restore original system style and palette
            app.setStyle(self.main_window.original_style_name)
            app.setPalette(self.main_window.original_palette)
            return

        # Map theme names to style keys
        theme_map = {
            "Basic": "windows",
            "Fusion": "Fusion",
            "Windows": "Windows",
            "WindowsVista": "WindowsVista",
            "Universal": "windowsvista",
            "Material": "Material"
        }

        parts = theme.split()
        variant = "Light"
        style_base_name = theme

        if len(parts) > 1 and parts[-1] in ["Light", "Dark"]:
            variant = parts[-1]
            style_base_name = " ".join(parts[:-1])

        style_key = theme_map.get(style_base_name, "Fusion")

        available_styles = [s.lower() for s in QStyleFactory.keys()]
        if style_key.lower() not in available_styles:
            logging.warning(f"Style '{style_key}' not found. Falling back to 'Fusion'.")
            style_key = "Fusion"

        app.setStyle(style_key)

        if variant == "Dark":
            app.setPalette(self._create_dark_palette())
        else:  # Light
            app.setPalette(app.style().standardPalette())

    def sync_ui_from_config(self, config: AppConfig):
        self.blockSignals(True)

        self.source_dirs_list.clear()
        self.source_dirs_list.addItems(config.source_dirs)
        self.excluded_dirs_list.clear()
        self.excluded_dirs_list.addItems(config.excluded_dirs)
        self.other_managers_combo.setCurrentText(config.game_managers_present)
        self.exclude_manager_checkbox.setChecked(config.exclude_selected_manager_games)
        self.logging_verbosity_combo.setCurrentText(config.logging_verbosity)
        self.font_combo.setCurrentText(config.app_font)
        self.theme_combo.setCurrentText(config.app_theme)
        self.font_size_spin.setValue(config.font_size)

        for attr_name in self.PATH_ATTRIBUTES:
            if attr_name in self.path_rows:
                row = self.path_rows[attr_name]
                row.path = getattr(config, attr_name, "")
                row.mode = config.deployment_path_modes.get(attr_name, "CEN")
                row.enabled = config.defaults.get(f"{attr_name}_enabled", True)
                row.run_wait = config.run_wait_states.get(f"{attr_name}_run_wait", False)

        self.launch_sequence_list.clear()
        self.launch_sequence_list.addItems(config.launch_sequence if config.launch_sequence else 
            ["Controller-Mapper", "Monitor-Config", "No-TB", "Pre1", "Pre2", "Pre3", "Borderless"])
        self.exit_sequence_list.clear()
        self.exit_sequence_list.addItems(config.exit_sequence if config.exit_sequence else
            ["Post1", "Post2", "Post3", "Monitor-Config", "Taskbar", "Controller-Mapper"])

        self.blockSignals(False)

    def sync_config_from_ui(self, config: AppConfig):
        config.source_dirs = [self.source_dirs_list.item(i).text() for i in range(self.source_dirs_list.count())]
        config.excluded_dirs = [self.excluded_dirs_list.item(i).text() for i in range(self.excluded_dirs_list.count())]
        config.game_managers_present = self.other_managers_combo.currentText()
        config.exclude_selected_manager_games = self.exclude_manager_checkbox.isChecked()
        config.logging_verbosity = self.logging_verbosity_combo.currentText()
        config.app_font = self.font_combo.currentText()
        config.app_theme = self.theme_combo.currentText()
        config.font_size = self.font_size_spin.value()

        for attr_name in self.PATH_ATTRIBUTES:
            if attr_name in self.path_rows:
                row = self.path_rows[attr_name]
                setattr(config, attr_name, row.path)
                config.deployment_path_modes[attr_name] = row.mode
                if row.enabled_cb:
                    config.defaults[f"{attr_name}_enabled"] = row.enabled
                if row.run_wait_cb:
                    config.run_wait_states[f"{attr_name}_run_wait"] = row.run_wait

        config.launch_sequence = [self.launch_sequence_list.item(i).text() for i in range(self.launch_sequence_list.count())]
        config.exit_sequence = [self.exit_sequence_list.item(i).text() for i in range(self.exit_sequence_list.count())]