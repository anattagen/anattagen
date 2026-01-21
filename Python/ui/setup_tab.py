import logging
import os
import configparser
import requests
import zipfile
import shutil
import subprocess
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QLabel, QFormLayout, QPushButton,
    QComboBox, QHBoxLayout, QCheckBox, QTabWidget,
    QFileDialog, QApplication, QSpinBox, QMessageBox, QMenu,
    QDialog, QDialogButtonBox, QLineEdit, QProgressDialog, QGridLayout
)
from PyQt6.QtGui import QFontDatabase, QFont, QPalette, QColor
from PyQt6.QtCore import pyqtSignal, Qt, QThread, pyqtSlot
from Python.models import AppConfig
from Python.ui.widgets import DragDropListWidget, PathConfigRow
from Python.ui.accordion import AccordionSection
from Python import constants
from .theme.gui.core import json_settings, json_themes
class DownloadThread(QThread):
    """Thread for downloading and extracting tools."""
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool, str, str) # success, message, result_path

    def __init__(self, url, extract_dir, exe_name):
        super().__init__()
        self.url = url
        self.extract_dir = extract_dir
        self.exe_name = exe_name

    def _extract_with_7z(self, archive_path):
        """Fallback extraction using 7z.exe."""
        seven_z_exe = os.path.join(constants.APP_ROOT_DIR, "bin", "7z.exe")
        if os.path.exists(seven_z_exe):
            cmd = [
                seven_z_exe, 
                "x", 
                archive_path, 
                f"-o{self.extract_dir}", 
                "-y"
            ]
            subprocess.run(cmd, check=True, creationflags=0x08000000) # CREATE_NO_WINDOW
            os.remove(archive_path)
        else:
            raise FileNotFoundError(f"7z.exe not found at {seven_z_exe} and py7zr module not installed.")

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
            
            # Validate file size (prevent processing of 404 pages or small error files)
            file_size = os.path.getsize(save_path)
            if file_size < 1024:
                with open(save_path, 'r', errors='ignore') as f:
                    preview = f.read(100).strip()
                os.remove(save_path)
                raise Exception(f"Downloaded file is too small ({file_size} bytes). Likely an error page: {preview}")
            
            # Extract if it's a zip
            if filename.lower().endswith('.zip'):
                with zipfile.ZipFile(save_path, 'r') as zip_ref:
                    zip_ref.extractall(self.extract_dir)
                os.remove(save_path) # Clean up zip
            elif filename.lower().endswith('.7z'):
                # Try py7zr first (Pure Python)
                try:
                    import py7zr
                    with py7zr.SevenZipFile(save_path, mode='r') as z:
                        z.extractall(path=self.extract_dir)
                    os.remove(save_path)
                except (ImportError, Exception):
                    # Fallback to 7z.exe
                    self._extract_with_7z(save_path)
            elif filename.lower().endswith('.rar'):
                self._extract_with_7z(save_path)
                
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
    setting_changed = pyqtSignal(str)
    
    PATH_ATTRIBUTES = [
        "profiles_dir", "launchers_dir", "launcher_executable", "controller_mapper_path", 
        "borderless_gaming_path", "multi_monitor_tool_path",
        "p1_profile_path", "p2_profile_path", "mediacenter_profile_path",
        "multimonitor_gaming_path", "multimonitor_media_path",
        "pre1_path", "pre2_path", "pre3_path",
        "just_after_launch_path", "just_before_exit_path",
        "post1_path", "post2_path", "post3_path"
    ]

    SEQUENCE_TOOLTIPS = {
        "Kill-Game": "Terminates the game process if it's running.",
        "Kill-List": "Terminates processes specified in the Kill List.",
        "Mount-Iso": "Mounts the game ISO if configured.",
        "Unmount-Iso": "Unmounts the game ISO.",
        "Controller-Mapper": "Starts/Stops the controller mapper (e.g. AntimicroX).",
        "Monitor-Config": "Applies monitor configuration (Game/Desktop).",
        "No-TB": "Hides the Windows Taskbar.",
        "Taskbar": "Restores the Windows Taskbar.",
        "Pre1": "Runs Pre-Launch Script 1.",
        "Pre2": "Runs Pre-Launch Script 2.",
        "Pre3": "Runs Pre-Launch Script 3.",
        "Post1": "Runs Post-Launch Script 1.",
        "Post2": "Runs Post-Launch Script 2.",
        "Post3": "Runs Post-Launch Script 3.",
        "Borderless": "Starts/Stops Borderless Gaming.",
        "Cloud-Sync": "Runs the Cloud Sync application.",
    }
    def apply_selected_theme(self, theme_name: str):
        """Applies the selected JSON theme to the current UI."""
        if not theme_name:
            return

        themes_dir = os.path.join(os.path.dirname(__file__), "theme", "gui", "themes")
        theme_file = os.path.join(themes_dir, f"{theme_name}.json")

        if not os.path.exists(theme_file):
            print(f"Theme not found: {theme_file}")
            return

        # Load framework settings
        json_settings.Settings()  # auto-load settings

        # Load the theme JSON
        theme_engine = json_themes.JsonThemes()

        # Detect correct method to load theme
        if hasattr(theme_engine, "load_theme"):
            theme_engine.load_theme(theme_file)
        elif hasattr(theme_engine, "set_theme"):
            theme_engine.set_theme(theme_file)
        elif hasattr(theme_engine, "load"):
            theme_engine.load(theme_file)
        else:
            raise RuntimeError("Unsupported JsonThemes API in your framework.")

        # Apply the generated stylesheet to the QApplication
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(theme_engine.stylesheet)
        else:
            print("No QApplication instance found; cannot apply theme")
    def __init__(self, parent=None): # parent is main_window
        super().__init__(parent)
        self.main_window = parent
        self.path_rows = {}
        self.repos = self._parse_repos_set()
        self.last_detected_tools = {}
        self.options_args_map = self._parse_options_arguments_set()
        self.download_thread = None
        self._setup_ui()

    def _add_path_row(self, layout, label_text, config_key, row_widget):
        """Helper to add a row with a context-menu-capable label."""
        formatted_text = f"{label_text}"
        label = QLabel(formatted_text)
        label.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        label.setToolTip("Right-click to configure Options & Arguments")
        label.customContextMenuRequested.connect(lambda pos: self._show_options_args_dialog(pos, config_key, label_text))
        layout.addRow(label, row_widget)

    def _setup_ui(self):
        """Create and arrange all widgets for the Setup tab."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # --- Section 1: Sources & Indexing ---
        source_config_widget = QWidget()
        source_config_layout = QGridLayout(source_config_widget)
        source_config_layout.setSpacing(10)

        # Sources
        self.source_dirs_list = DragDropListWidget()
        self.source_dirs_list.setMaximumHeight(100)
        
        source_label = QLabel("Source Directories:")
        add_source_button = QPushButton("Add...")
        add_source_button.setToolTip("Add a directory to scan for games.")
        remove_source_button = QPushButton("Remove")
        remove_source_button.setToolTip("Remove the selected directory from scanning.")
        
        # Left side: Label + Buttons
        source_left_container = QWidget()
        source_left_layout = QVBoxLayout(source_left_container)
        source_left_layout.setContentsMargins(0, 0, 0, 0)
        source_left_layout.addWidget(source_label)
        source_left_layout.addWidget(add_source_button)
        source_left_layout.addWidget(remove_source_button)
        source_left_layout.addStretch()
        
        source_config_layout.addWidget(source_left_container, 0, 0)
        source_config_layout.addWidget(self.source_dirs_list, 0, 1)
        
        self.add_source_dir_button = add_source_button
        self.remove_source_dir_button = remove_source_button

        # Excluded Items
        self.excluded_dirs_list = DragDropListWidget()
        self.excluded_dirs_list.setMaximumHeight(25)
        
        excluded_label = QLabel("Excluded Directories:")
        add_excluded_button = QPushButton("Add...")
        add_excluded_button.setToolTip("Add a directory to exclude from scanning.")
        remove_excluded_button = QPushButton("Remove")
        remove_excluded_button.setToolTip("Remove the selected directory from exclusion.")
        
        # Right side: Label + Buttons
        excluded_right_container = QWidget()
        excluded_right_layout = QVBoxLayout(excluded_right_container)
        excluded_right_layout.setContentsMargins(0, 0, 0, 0)
        excluded_right_layout.addWidget(excluded_label)
        excluded_right_layout.addWidget(add_excluded_button)
        excluded_right_layout.addWidget(remove_excluded_button)
        excluded_right_layout.addStretch()
        
        source_config_layout.addWidget(self.excluded_dirs_list, 1, 0)
        source_config_layout.addWidget(excluded_right_container, 1, 1)
        
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
        
        source_config_layout.addWidget(QLabel("Game Managers Present"), 2, 0)
        source_config_layout.addLayout(game_managers_layout, 2, 1)
        
        # Set column stretch to allow lists to expand
        source_config_layout.setColumnStretch(0, 1)
        source_config_layout.setColumnStretch(1, 1)

        source_config_section = AccordionSection("SOURCES AND INDEXING", source_config_widget)

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
        core_paths_layout = QVBoxLayout(core_paths_widget)
        
        # Directories Group
        directories_group = QGroupBox("Directories")
        directories_layout = QFormLayout(directories_group)
        self.path_rows["profiles_dir"] = PathConfigRow("profiles_dir", is_directory=True, add_enabled=True, add_cen_lc=True)
        self.path_rows["profiles_dir"].enabled_cb.setToolTip("Create Profile Folders")
        directories_layout.addRow("Profiles Directory:", self.path_rows["profiles_dir"]) # No options/args for dirs
        self.path_rows["launchers_dir"] = PathConfigRow("launchers_dir", is_directory=True, add_enabled=True, add_cen_lc=True)
        self.path_rows["launchers_dir"].enabled_cb.setToolTip("Create Launcher")
        directories_layout.addRow("Launchers Directory:", self.path_rows["launchers_dir"]) # No options/args for dirs
        core_paths_layout.addWidget(directories_group)

        # Launcher Configuration Group
        launcher_group = QGroupBox("Launcher Configuration")
        launcher_layout = QFormLayout(launcher_group)
        self.path_rows["launcher_executable"] = PathConfigRow("launcher_executable", is_directory=False, add_enabled=False, add_cen_lc=True)
        self.path_rows["launcher_executable"].line_edit.setPlaceholderText(constants.LAUNCHER_EXECUTABLE)
        self._add_path_row(launcher_layout, "Launcher Executable:", "launcher_executable", self.path_rows["launcher_executable"])

        # Moved checkboxes from Deployment Tab
        self.run_as_admin_checkbox = QCheckBox("Run As Admin")
        self.use_kill_list_checkbox = QCheckBox("Use Kill List")
        self.hide_taskbar_checkbox = QCheckBox("Hide Taskbar")
        self.terminate_bw_on_exit_checkbox = QCheckBox("Terminate Borderless on Exit")

        cb_container = QWidget()
        cb_layout = QGridLayout(cb_container)
        cb_layout.setContentsMargins(0, 0, 0, 0)
        cb_layout.addWidget(self.run_as_admin_checkbox, 0, 0)
        cb_layout.addWidget(self.use_kill_list_checkbox, 0, 1)
        cb_layout.addWidget(self.hide_taskbar_checkbox, 1, 0)
        cb_layout.addWidget(self.terminate_bw_on_exit_checkbox, 1, 1)
        launcher_layout.addRow(cb_container)
        
        core_paths_layout.addWidget(launcher_group)
        core_paths_layout.addStretch()

        paths_tabs.addTab(core_paths_widget, "   CORE   ")

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
        paths_tabs.addTab(app_paths_widget, "APPLICATIONS")

        # Profile Paths Tab
        profile_paths_widget = QWidget()
        profile_paths_layout = QFormLayout(profile_paths_widget)
        self.path_rows["p1_profile_path"] = PathConfigRow("p1_profile_path", add_enabled=True)
        profile_paths_layout.addRow("Player 1 Profile:", self.path_rows["p1_profile_path"])
        self.path_rows["p2_profile_path"] = PathConfigRow("p2_profile_path", add_enabled=True)
        profile_paths_layout.addRow("Player 2 Profile:", self.path_rows["p2_profile_path"])
        self.path_rows["mediacenter_profile_path"] = PathConfigRow("mediacenter_profile_path", add_enabled=True)
        profile_paths_layout.addRow("MediaCenter Profile:", self.path_rows["mediacenter_profile_path"])
        self.path_rows["multimonitor_gaming_path"] = PathConfigRow("multimonitor_gaming_path", add_enabled=True)
        profile_paths_layout.addRow("MM Gaming Config:", self.path_rows["multimonitor_gaming_path"])
        self.path_rows["multimonitor_media_path"] = PathConfigRow("multimonitor_media_path", add_enabled=True)
        profile_paths_layout.addRow("MM Desktop Config:", self.path_rows["multimonitor_media_path"])
        paths_tabs.addTab(profile_paths_widget, "   PROFILES   ")

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
        paths_tabs.addTab(script_paths_widget, "   SCRIPTS   ")
        
        paths_section = AccordionSection("PATHS AND PROFILES", paths_widget)

        # --- Section 3: Execution Sequence ---
        sequences_widget = QWidget()
        sequences_layout = QHBoxLayout(sequences_widget)

        # Launch Sequence
        launch_sequence_group = QGroupBox("LAUNCH ORDER")
        launch_sequence_layout = QVBoxLayout(launch_sequence_group)
        self.launch_sequence_list = DragDropListWidget()
        self.launch_sequence_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.launch_sequence_list.customContextMenuRequested.connect(lambda pos: self._on_sequence_context_menu(pos, self.launch_sequence_list, "launch"))
        self.reset_launch_btn = QPushButton("Reset")
        launch_sequence_layout.addWidget(self.launch_sequence_list)
        launch_sequence_layout.addWidget(self.reset_launch_btn)
        sequences_layout.addWidget(launch_sequence_group)

        # Exit Sequence
        exit_sequence_group = QGroupBox("EXIT ORDER")
        exit_sequence_layout = QVBoxLayout(exit_sequence_group)
        self.exit_sequence_list = DragDropListWidget()
        self.exit_sequence_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.exit_sequence_list.customContextMenuRequested.connect(lambda pos: self._on_sequence_context_menu(pos, self.exit_sequence_list, "exit"))
        self.reset_exit_btn = QPushButton("Reset")
        exit_sequence_layout.addWidget(self.exit_sequence_list)
        exit_sequence_layout.addWidget(self.reset_exit_btn)
        sequences_layout.addWidget(exit_sequence_group)
        sequences_section = AccordionSection("EXECUTION SEQUENCES", sequences_widget)

        # --- Section 4: Appearance & Behavior ---
        appearance_widget = QWidget()
        appearance_layout = QFormLayout(appearance_widget)
        # Logging Verbosity
        self.logging_verbosity_combo = QComboBox()
        self.logging_verbosity_combo.addItems(["None", "Low", "Medium", "High", "Debug"])
        appearance_layout.addRow("LOGGING VERBOSITY:", self.logging_verbosity_combo)
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
        self.theme_combo.addItems(["System", "Dark", "Light", "Auto", "Midnight", "Ocean"])
        themes_dir = os.path.join(os.path.dirname(__file__), "theme", "gui", "themes")
        available_themes = [
            f.replace(".json", "") for f in os.listdir(themes_dir) if f.endswith(".json")
        ] 
        self.theme_combo.addItems(sorted(available_themes))
        appearance_layout.addRow("Theme:", self.theme_combo)
        try:
            settings = json_settings.Settings()
            current_theme = getattr(settings, "theme_name", "default")
        except Exception:
            current_theme = "default"

    # Set combo box to current theme
        if current_theme in self.available_themes:
            index = self.available_themes.index(current_theme)
            self.theme_combo.setCurrentIndex(index)

    # Connect signal to apply theme on selection
        self.theme_combo.currentTextChanged.connect(self.apply_selected_theme)
    # --- end theme combo setup ---
        
        # Editor Page Size
        self.page_size_spin = QSpinBox()
        self.page_size_spin.setRange(75, 2000)
        self.page_size_spin.setValue(150)
        self.page_size_spin.setToolTip("Number of rows per page in the Editor tab (75-2000)")
        appearance_layout.addRow("Editor Page Size:", self.page_size_spin)
        # Restart Button
        self.restart_btn = QPushButton("Reset to Defaults")
        self.restart_btn.setToolTip("Reset all application configuration to defaults")
        appearance_layout.addRow(self.restart_btn)
        appearance_section = AccordionSection("APPEARANCE AND BEHAVIOR", appearance_widget)

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
        
        # Determine defaults based on the current executable path
        current_path = getattr(self.main_window.config, config_key, "")
        exe_name = os.path.basename(current_path).lower() if current_path else ""
        
        # Mutable container for defaults
        defaults_state = {
            'opts': "",
            'args': "",
            'has_defaults': False
        }
        
        if exe_name in self.options_args_map:
            defaults_state['opts'], defaults_state['args'] = self.options_args_map[exe_name]
            defaults_state['has_defaults'] = True

        options_edit = QLineEdit()
        options_edit.setText(getattr(self.main_window.config, f"{config_key}_options", ""))
        layout.addRow("Options:", options_edit)
        
        args_edit = QLineEdit()
        args_edit.setText(getattr(self.main_window.config, f"{config_key}_arguments", ""))
        layout.addRow("Arguments:", args_edit)
        
        # Visual indicator for defaults match
        status_label = QLabel()
        layout.addRow("", status_label)

        def check_defaults():
            if not defaults_state['has_defaults']:
                status_label.setText("")
                return
            
            is_match = (options_edit.text() == defaults_state['opts'] and 
                        args_edit.text() == defaults_state['args'])
            
            if is_match:
                status_label.setText("✓ Matches defaults")
                status_label.setStyleSheet("color: green;")
            else:
                status_label.setText("⚠ Custom values")
                status_label.setStyleSheet("color: orange;")

        options_edit.textChanged.connect(check_defaults)
        args_edit.textChanged.connect(check_defaults)
        
        # Initial check
        check_defaults()

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        
        # Add Reset button
        reset_btn = buttons.addButton("Reset to Defaults", QDialogButtonBox.ButtonRole.ResetRole)
        reset_btn.setVisible(defaults_state['has_defaults'])
        
        def reset_values():
            if defaults_state['has_defaults']:
                options_edit.setText(defaults_state['opts'])
                args_edit.setText(defaults_state['args'])
        reset_btn.clicked.connect(reset_values)

        # Function to update defaults if path changes while dialog is open
        def update_defaults_from_path():
            if config_key in self.path_rows:
                curr_path = self.path_rows[config_key].line_edit.text()
            else:
                curr_path = ""
            
            curr_exe = os.path.basename(curr_path).lower() if curr_path else ""
            
            if curr_exe in self.options_args_map:
                defaults_state['opts'], defaults_state['args'] = self.options_args_map[curr_exe]
                defaults_state['has_defaults'] = True
            else:
                defaults_state['opts'], defaults_state['args'] = "", ""
                defaults_state['has_defaults'] = False
            
            check_defaults()
            reset_btn.setVisible(defaults_state['has_defaults'])

        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        self._current_dialog_key = config_key
        self._current_dialog_updater = update_defaults_from_path
        
        try:
            if dialog.exec():
                setattr(self.main_window.config, f"{config_key}_options", options_edit.text())
                setattr(self.main_window.config, f"{config_key}_arguments", args_edit.text())
                self.config_changed.emit()
        finally:
            self._current_dialog_key = None
            self._current_dialog_updater = None

    def _connect_signals(self):
        self.add_source_dir_button.clicked.connect(self._add_source_dir)
        self.remove_source_dir_button.clicked.connect(self._remove_source_dir)
        self.add_excluded_dir_button.clicked.connect(self._add_excluded_dir)
        self.remove_excluded_dir_button.clicked.connect(self._remove_excluded_dir)
        self.reset_launch_btn.clicked.connect(self._reset_launch_sequence)
        self.reset_exit_btn.clicked.connect(self._reset_exit_sequence)

        self.run_as_admin_checkbox.stateChanged.connect(self.config_changed.emit)
        self.use_kill_list_checkbox.stateChanged.connect(self.config_changed.emit)
        self.hide_taskbar_checkbox.stateChanged.connect(self.config_changed.emit)
        self.terminate_bw_on_exit_checkbox.stateChanged.connect(self.config_changed.emit)

        self.source_dirs_list.model().rowsMoved.connect(self.config_changed.emit)
        self.source_dirs_list.model().rowsInserted.connect(self.config_changed.emit)
        self.source_dirs_list.model().rowsRemoved.connect(self.config_changed.emit)
        self.excluded_dirs_list.model().rowsMoved.connect(self.config_changed.emit)
        self.excluded_dirs_list.model().rowsInserted.connect(lambda: self.config_changed.emit())
        self.excluded_dirs_list.model().rowsRemoved.connect(self.config_changed.emit)
        # Path rows
        for key, row in self.path_rows.items():
            row.valueChanged.connect(self.config_changed.emit)
            row.valueChanged.connect(lambda k=key: self.setting_changed.emit(k))
            row.downloadRequested.connect(self._on_download_requested)
        
        for key, row in self.path_rows.items():
            row.line_edit.textChanged.connect(lambda text, k=key: self._on_path_text_changed(k, text))

        # Sequences
        self.launch_sequence_list.model().layoutChanged.connect(self.config_changed.emit)
        self.exit_sequence_list.model().layoutChanged.connect(self.config_changed.emit)

        # Logging
        self.logging_verbosity_combo.currentTextChanged.connect(self.main_window._on_logging_verbosity_changed)
        
        # Appearance
        self.font_combo.currentTextChanged.connect(self._on_appearance_changed)
        self.font_size_spin.valueChanged.connect(self._on_appearance_changed)
        self.theme_combo.currentTextChanged.connect(self._on_appearance_changed)
        self.page_size_spin.valueChanged.connect(self.config_changed.emit)
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
            repos[section.upper()] = {}
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
                    url = parts[0]
                    # Fix common GitHub URL malformation where refs/heads/ is included in raw link
                    if "github.com" in url and "/raw/refs/heads/" in url:
                        url = url.replace("/raw/refs/heads/", "/raw/")

                    repos[section.upper()][key] = {
                        'url': url,
                        'extract_dir': parts[1],
                        'exe_name': parts[2]
                    }
        return repos

    def _parse_options_arguments_set(self):
        """Parses the options_arguments.set file and returns a dictionary."""
        mapping = {}
        if not os.path.exists(constants.OPTIONS_ARGUMENTS_SET):
            return mapping
        
        config = configparser.ConfigParser()
        try:
            with open(constants.OPTIONS_ARGUMENTS_SET, 'r', encoding='utf-8-sig') as f:
                config.read_file(f)
            for section in config.sections():
                options = config.get(section, 'options', fallback="").strip()
                arguments = config.get(section, 'arguments', fallback="").strip()
                mapping[section.lower()] = (options, arguments)
        except Exception as e:
            logging.error(f"Error parsing options_arguments.set: {e}")
        return mapping

    def _on_download_requested(self, tool_name, tool_data):
        if self.download_thread and self.download_thread.isRunning():
            QMessageBox.warning(self, "Download in Progress", "Please wait for the current download to finish.")
            return

        # Check if files exist
        extract_dir = tool_data['extract_dir']
        exe_name = tool_data['exe_name']
        url = tool_data['url']
        
        exe_path = os.path.join(extract_dir, exe_name)
        zip_name = url.split('/')[-1]
        zip_path = os.path.join(extract_dir, zip_name)
        
        if os.path.exists(exe_path) or os.path.exists(zip_path):
            reply = QMessageBox.question(
                self, "File Exists",
                f"The tool '{tool_name}' appears to be already downloaded.\n"
                "Do you want to download and overwrite it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        self.active_download_row = self.sender() # Store the row that requested the download
        
        # Use QProgressDialog instead of embedded bar
        self.progress_dialog = QProgressDialog(f"Downloading {tool_name}...", "Cancel", 0, 100, self)
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setAutoClose(False)
        self.progress_dialog.show()

        self.download_thread = DownloadThread(tool_data['url'], tool_data['extract_dir'], tool_data['exe_name'])
        self.download_thread.progress.connect(self.progress_dialog.setValue)
        self.download_thread.finished.connect(self._on_download_finished_slot)
        self.download_thread.start()

    def _on_download_finished_slot(self, success, message, result_path):
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()
            
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
        self.launch_sequence_list.addItems(["Kill-Game", "Kill-List", "Mount-Iso", "Controller-Mapper", "Monitor-Config", "No-TB", "Pre1", "Borderless", "Pre2", "Pre3"])
        self.config_changed.emit()
        self._update_list_tooltips(self.launch_sequence_list)

    def _reset_exit_sequence(self):
        self.exit_sequence_list.clear()
        self.exit_sequence_list.addItems(["Kill-Game", "Kill-List", "Unmount-Iso", "Monitor-Config", "Taskbar", "Post1", "Controller-Mapper", "Post2", "Borderless", "Post3"])
        self.config_changed.emit()
        self._update_list_tooltips(self.exit_sequence_list)

    def _on_appearance_changed(self):
        self.config_changed.emit()
        self._apply_visual_settings()

    def _on_sequence_context_menu(self, pos, list_widget, sequence_type):
        item = list_widget.itemAt(pos)

        menu = QMenu(self)
        
        # Define full sets
        if sequence_type == "launch":
            full_set = ["Kill-Game", "Kill-List", "Mount-Iso", "Controller-Mapper", "Monitor-Config", "No-TB", "Pre1", "Pre2", "Pre3", "Borderless", "Cloud-Sync"]
        else:
            full_set = ["Kill-Game", "Kill-List", "Unmount-Iso", "Monitor-Config", "Taskbar", "Post1", "Post2", "Post3", "Controller-Mapper", "Borderless", "Cloud-Sync"]
            
        current_items = [list_widget.item(i).text() for i in range(list_widget.count())]
        removed_items = [x for x in full_set if x not in current_items]
        
        if item:
            # Remove
            remove_action = menu.addAction("Remove")
            remove_action.triggered.connect(lambda: self._remove_sequence_item(list_widget, item))
            
            # Swap
            swap_menu = menu.addMenu("Swap with")
            current_row = list_widget.row(item)
            for i in range(list_widget.count()):
                if i == current_row:
                    continue
                other_item = list_widget.item(i)
                action = swap_menu.addAction(other_item.text())
                action.triggered.connect(lambda checked, r1=current_row, r2=i: self._swap_sequence_items(list_widget, r1, r2))
            
            menu.addSeparator()
            
            move_up = menu.addAction("Move Up")
            move_up.triggered.connect(lambda: self._move_sequence_item(list_widget, item, -1))
            
            move_down = menu.addAction("Move Down")
            move_down.triggered.connect(lambda: self._move_sequence_item(list_widget, item, 1))
            
            if current_row == 0:
                move_up.setEnabled(False)
            if current_row == list_widget.count() - 1:
                move_down.setEnabled(False)

            # Replace (with removed items)
            replace_menu = menu.addMenu("Replace with")
            
            if not removed_items:
                replace_menu.setDisabled(True)
            else:
                for removed in removed_items:
                    action = replace_menu.addAction(removed)
                    action.triggered.connect(lambda checked, it=item, txt=removed: self._replace_sequence_item(list_widget, it, txt))
            
            menu.addSeparator()

        # Add (append from removed items)
        add_menu = menu.addMenu("Add")
        if not removed_items:
            add_menu.setDisabled(True)
        else:
            for removed in removed_items:
                action = add_menu.addAction(removed)
                action.triggered.connect(lambda checked, txt=removed: self._add_sequence_item(list_widget, txt))

        if not menu.isEmpty():
            menu.exec(list_widget.mapToGlobal(pos))

    def _remove_sequence_item(self, list_widget, item):
        list_widget.takeItem(list_widget.row(item))
        self.config_changed.emit()

    def _add_sequence_item(self, list_widget, text):
        list_widget.addItem(text)
        # Set tooltip for the new item
        item = list_widget.item(list_widget.count() - 1)
        self._update_item_tooltip(item)
        self.config_changed.emit()

    def _swap_sequence_items(self, list_widget, row1, row2):
        item1 = list_widget.item(row1)
        item2 = list_widget.item(row2)
        text1 = item1.text()
        text2 = item2.text()
        item1.setText(text2)
        item2.setText(text1)
        self._update_item_tooltip(item1)
        self._update_item_tooltip(item2)
        self.config_changed.emit()

    def _replace_sequence_item(self, list_widget, item, new_text):
        item.setText(new_text)
        self._update_item_tooltip(item)
        self.config_changed.emit()

    def _move_sequence_item(self, list_widget, item, direction):
        row = list_widget.row(item)
        new_row = row + direction
        if 0 <= new_row < list_widget.count():
            current_item = list_widget.takeItem(row)
            list_widget.insertItem(new_row, current_item)
            list_widget.setCurrentItem(current_item)
            self.config_changed.emit()

    def _update_item_tooltip(self, item):
        text = item.text()
        if text in self.SEQUENCE_TOOLTIPS:
            item.setToolTip(self.SEQUENCE_TOOLTIPS[text])
        else:
            item.setToolTip("")

    def _update_list_tooltips(self, list_widget):
        for i in range(list_widget.count()):
            self._update_item_tooltip(list_widget.item(i))

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

    def _create_midnight_palette(self):
        """Creates a QPalette for a Midnight (blue-black) theme."""
        p = QPalette()
        p.setColor(QPalette.ColorRole.Window, QColor(15, 15, 30))
        p.setColor(QPalette.ColorRole.WindowText, QColor(220, 220, 220))
        p.setColor(QPalette.ColorRole.Base, QColor(10, 10, 20))
        p.setColor(QPalette.ColorRole.AlternateBase, QColor(20, 20, 40))
        p.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 220))
        p.setColor(QPalette.ColorRole.ToolTipText, QColor(0, 0, 0))
        p.setColor(QPalette.ColorRole.Text, QColor(220, 220, 220))
        p.setColor(QPalette.ColorRole.Button, QColor(25, 25, 50))
        p.setColor(QPalette.ColorRole.ButtonText, QColor(220, 220, 220))
        p.setColor(QPalette.ColorRole.Link, QColor(80, 180, 255))
        p.setColor(QPalette.ColorRole.Highlight, QColor(60, 80, 140))
        p.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        return p

    def _create_ocean_palette(self):
        """Creates a QPalette for an Ocean (teal/slate) theme."""
        p = self._create_dark_palette() # Start with dark base
        p.setColor(QPalette.ColorRole.Window, QColor(30, 45, 50))
        p.setColor(QPalette.ColorRole.Base, QColor(20, 30, 35))
        p.setColor(QPalette.ColorRole.AlternateBase, QColor(35, 50, 55))
        p.setColor(QPalette.ColorRole.Button, QColor(40, 60, 65))
        p.setColor(QPalette.ColorRole.Highlight, QColor(0, 150, 136)) # Teal highlight
        p.setColor(QPalette.ColorRole.Link, QColor(0, 188, 212))
        return p

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

        if theme == "Midnight":
            app.setStyle("Fusion")
            app.setPalette(self._create_midnight_palette())
            return
        elif theme == "Ocean":
            app.setStyle("Fusion")
            app.setPalette(self._create_ocean_palette())
            return

        try:
            import qdarktheme
            theme_key = theme.lower()
            if theme_key not in ["dark", "light", "auto"]:
                theme_key = "dark"

            if hasattr(qdarktheme, "setup_theme"):
                qdarktheme.setup_theme(theme_key)
            elif hasattr(qdarktheme, "load_stylesheet"):
                if theme_key == "auto": theme_key = "dark"
                app.setStyleSheet(qdarktheme.load_stylesheet(theme_key))
        except Exception as e:
            logging.warning(f"pyqtdarktheme module error: {e}. Falling back to Fusion.")
            app.setStyle("Fusion")
            if "Dark" in theme or theme == "Dark":
                app.setPalette(self._create_dark_palette())
            else:
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
        
        self.run_as_admin_checkbox.setChecked(config.run_as_admin)
        self.use_kill_list_checkbox.setChecked(config.use_kill_list)
        self.hide_taskbar_checkbox.setChecked(config.hide_taskbar)
        self.terminate_bw_on_exit_checkbox.setChecked(config.terminate_borderless_on_exit)

        # Handle legacy themes
        theme = config.app_theme
        if theme not in ["System", "Dark", "Light", "Auto", "Midnight", "Ocean"]:
            if "Dark" in theme:
                theme = "Dark"
            elif "Light" in theme:
                theme = "Light"
            else:
                theme = "Dark"
        self.theme_combo.setCurrentText(theme)
        
        self.font_size_spin.setValue(config.font_size)
        self.page_size_spin.setValue(config.editor_page_size)

        for attr_name in self.PATH_ATTRIBUTES:
            if attr_name in self.path_rows:
                row = self.path_rows[attr_name]
                row.path = getattr(config, attr_name, "")
                row.mode = config.deployment_path_modes.get(attr_name, "CEN")
                
                # Default state logic: Uncheck if path is empty, unless it's a core directory
                if not row.path and attr_name not in ["profiles_dir", "launchers_dir"]:
                    row.enabled = False
                else:
                    row.enabled = config.defaults.get(f"{attr_name}_enabled", True)

                row.run_wait = config.run_wait_states.get(f"{attr_name}_run_wait", False)

                # Initialize last detected tool to prevent overwrite on load/sync
                if row.path:
                    exe_name = os.path.basename(row.path).lower()
                    exe_no_ext = os.path.splitext(exe_name)[0]
                    if exe_name in self.options_args_map:
                        self.last_detected_tools[attr_name] = exe_name
                    elif exe_no_ext in self.options_args_map:
                        self.last_detected_tools[attr_name] = exe_no_ext
                    else:
                        self.last_detected_tools[attr_name] = exe_name

        self.launch_sequence_list.clear()
        self.launch_sequence_list.addItems(config.launch_sequence if config.launch_sequence else 
            ["Controller-Mapper", "Monitor-Config", "No-TB", "Pre1", "Pre2", "Pre3", "Borderless"])
        self._update_list_tooltips(self.launch_sequence_list)
        
        self.exit_sequence_list.clear()
        self.exit_sequence_list.addItems(config.exit_sequence if config.exit_sequence else
            ["Post1", "Post2", "Post3", "Monitor-Config", "Taskbar", "Controller-Mapper"])
        self._update_list_tooltips(self.exit_sequence_list)

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
        config.editor_page_size = self.page_size_spin.value()

        config.run_as_admin = self.run_as_admin_checkbox.isChecked()
        config.use_kill_list = self.use_kill_list_checkbox.isChecked()
        config.hide_taskbar = self.hide_taskbar_checkbox.isChecked()
        config.terminate_borderless_on_exit = self.terminate_bw_on_exit_checkbox.isChecked()

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

    def _on_path_text_changed(self, config_key, new_path):
        """Updates options and arguments if the new path matches a known tool."""
        if not new_path:
            return
            
        exe_name = os.path.basename(new_path).lower()
        exe_no_ext = os.path.splitext(exe_name)[0]
        
        target = None
        if exe_name in self.options_args_map:
            target = exe_name
        elif exe_no_ext in self.options_args_map:
            target = exe_no_ext
            
        # Determine current tool identifier
        current_tool_id = target if target else exe_name
        
        # Check if tool changed
        last_tool_id = self.last_detected_tools.get(config_key)
        if last_tool_id == current_tool_id:
            return # Tool hasn't changed, preserve customizations

        # Update tracker
        self.last_detected_tools[config_key] = current_tool_id

        if target:
            opts, args = self.options_args_map[target]
                                 
            # Update config if fields exist
            config = self.main_window.config
            opt_key = f"{config_key}_options"
            arg_key = f"{config_key}_arguments"
            
            updated = False
            if hasattr(config, opt_key) and getattr(config, opt_key) != opts:
                setattr(config, opt_key, opts)
                updated = True
            if hasattr(config, arg_key) and getattr(config, arg_key) != args:
                setattr(config, arg_key, args)
                updated = True
                
            if updated:
                logging.info(f"Applied default options/args for {exe_name} to {config_key}")
                logging.info(f"Applied default options/args for {target} to {config_key}")

                self.config_changed.emit()
        
        # Update dialog if open
        if getattr(self, '_current_dialog_key', None) == config_key and hasattr(self, '_current_dialog_updater'):
            self._current_dialog_updater()