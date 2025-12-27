import os
import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QLabel, QFormLayout, QPushButton,
    QComboBox, QHBoxLayout, QCheckBox,
    QFileDialog, QApplication, QStyleFactory, QSpinBox, QMessageBox
)
from PyQt6.QtGui import QFontDatabase, QFont, QPalette, QColor
from PyQt6.QtCore import pyqtSignal, Qt
from Python.models import AppConfig
from Python.ui.widgets import DragDropListWidget, PathConfigRow
from Python.ui.accordion import AccordionSection
from Python import constants

class SetupTab(QWidget):
    """A QWidget that encapsulates all UI and logic for the Setup tab."""
    
    config_changed = pyqtSignal()
    
    PATH_ATTRIBUTES = [
        "profiles_dir", "launchers_dir", "controller_mapper_path", 
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
        self._setup_ui()

    def _setup_ui(self):
        """Create and arrange all widgets for the Setup tab."""
        main_layout = QVBoxLayout(self)

        # --- Section 0: Source Configuration ---
        source_config_widget = QWidget()
        source_config_layout = QVBoxLayout(source_config_widget)

        # Sources
        source_dirs_layout = QHBoxLayout()
        source_dirs_layout.addWidget(QLabel("Sources:"))
        self.source_dirs_list = DragDropListWidget()
        self.source_dirs_list.setMaximumHeight(100)
        source_dirs_layout.addWidget(self.source_dirs_list, 1)
        source_buttons_layout = QHBoxLayout()
        self.add_source_dir_button = QPushButton("Add...")
        self.remove_source_dir_button = QPushButton("Remove")
        source_buttons_layout.addWidget(self.add_source_dir_button)
        source_buttons_layout.addWidget(self.remove_source_dir_button)
        source_dirs_layout.addLayout(source_buttons_layout)
        source_config_layout.addLayout(source_dirs_layout)

        # Excluded Items
        excluded_layout = QHBoxLayout()
        excluded_layout.addWidget(QLabel("Excluded Items:"))
        self.excluded_dirs_list = DragDropListWidget()
        self.excluded_dirs_list.setMaximumHeight(100)
        excluded_layout.addWidget(self.excluded_dirs_list, 1)
        excluded_buttons_layout = QHBoxLayout()
        self.add_excluded_dir_button = QPushButton("+")
        self.add_excluded_dir_button.setFixedWidth(30)
        self.remove_excluded_dir_button = QPushButton("x")
        self.remove_excluded_dir_button.setFixedWidth(30)
        excluded_buttons_layout.addStretch(1)
        excluded_buttons_layout.addWidget(self.add_excluded_dir_button)
        excluded_buttons_layout.addWidget(self.remove_excluded_dir_button)
        excluded_layout.addLayout(excluded_buttons_layout)
        source_config_layout.addLayout(excluded_layout)

        # Game managers
        game_managers_layout = QHBoxLayout()
        game_managers_layout.addWidget(QLabel("Game Managers Present:"))
        self.other_managers_combo = QComboBox()
        self.other_managers_combo.addItems(["None", "Steam", "Epic", "GOG", "Origin", "Ubisoft Connect", "Battle.net", "Xbox"])
        game_managers_layout.addWidget(self.other_managers_combo)
        self.exclude_manager_checkbox = QCheckBox("Exclude Selected Manager's Games")
        game_managers_layout.addWidget(self.exclude_manager_checkbox)
        game_managers_layout.addStretch(1)
        source_config_layout.addLayout(game_managers_layout)

        # Logging Verbosity
        appearance_layout = QHBoxLayout()
        appearance_layout.addWidget(QLabel("Logging Verbosity:"))
        self.logging_verbosity_combo = QComboBox()
        self.logging_verbosity_combo.addItems(["None", "Low", "Medium", "High", "Debug"])
        appearance_layout.addWidget(self.logging_verbosity_combo)
        appearance_layout.addStretch()

        # Font Dropdown
        appearance_layout.addWidget(QLabel("Font:"))
        self.font_combo = QComboBox()
        self.font_combo.addItem("System")
        custom_fonts = self._load_and_get_custom_fonts()
        self.font_combo.addItems(custom_fonts)
        appearance_layout.addWidget(self.font_combo)

        # Font Size SpinBox
        appearance_layout.addWidget(QLabel("Size:"))
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(10)
        appearance_layout.addWidget(self.font_size_spin)

        # Theme Dropdown
        appearance_layout.addWidget(QLabel("Theme:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["System", "Fusion Dark"])
        available_styles = [s.lower() for s in QStyleFactory.keys()]
        if "material" in available_styles:
            self.theme_combo.addItems(["Material Light", "Material Dark"])
        appearance_layout.addWidget(self.theme_combo)

        # Restart Button
        self.restart_btn = QPushButton("*")
        self.restart_btn.setToolTip("Reset application configuration to defaults")
        self.restart_btn.setFixedWidth(25)
        appearance_layout.addWidget(self.restart_btn)
        source_config_layout.addLayout(appearance_layout)

        # --- Section 1: Directories ---
        directories_widget = QWidget()
        directories_layout = QFormLayout(directories_widget)
        self.path_rows["profiles_dir"] = PathConfigRow("profiles_dir", is_directory=True, add_enabled=False, add_cen_lc=False)
        directories_layout.addRow("Profiles Directory:", self.path_rows["profiles_dir"])
        self.path_rows["launchers_dir"] = PathConfigRow("launchers_dir", is_directory=True, add_enabled=False, add_cen_lc=False)
        directories_layout.addRow("Launchers Directory:", self.path_rows["launchers_dir"])

        # --- Section 2: Applications ---
        applications_widget = QWidget()
        applications_layout = QFormLayout(applications_widget)
        self.path_rows["controller_mapper_path"] = PathConfigRow("controller_mapper_path", add_run_wait=True)
        applications_layout.addRow("Controller Mapper:", self.path_rows["controller_mapper_path"])
        self.path_rows["borderless_gaming_path"] = PathConfigRow("borderless_gaming_path", add_run_wait=True)
        applications_layout.addRow("Borderless Windowing:", self.path_rows["borderless_gaming_path"])
        self.path_rows["multi_monitor_tool_path"] = PathConfigRow("multi_monitor_tool_path", add_run_wait=True)
        applications_layout.addRow("Multi-Monitor App:", self.path_rows["multi_monitor_tool_path"])
        
        for i in range(1, 4):
            key = f"pre{i}_path"
            self.path_rows[key] = PathConfigRow(key, add_run_wait=True)
            applications_layout.addRow(f"Pre-Launch App {i}:", self.path_rows[key])
        
        self.path_rows["just_after_launch_path"] = PathConfigRow("just_after_launch_path", add_run_wait=True)
        applications_layout.addRow("Just After Launch:", self.path_rows["just_after_launch_path"])
        
        self.path_rows["just_before_exit_path"] = PathConfigRow("just_before_exit_path", add_run_wait=True)
        applications_layout.addRow("Just Before Exit:", self.path_rows["just_before_exit_path"])

        for i in range(1, 4):
            key = f"post{i}_path"
            self.path_rows[key] = PathConfigRow(key, add_run_wait=True)
            applications_layout.addRow(f"Post-Launch App {i}:", self.path_rows[key])

        # --- Section 3: Profiles ---
        profiles_widget = QWidget()
        profiles_layout = QFormLayout(profiles_widget)
        self.path_rows["p1_profile_path"] = PathConfigRow("p1_profile_path", add_enabled=False)
        profiles_layout.addRow("Player 1 Profile:", self.path_rows["p1_profile_path"])
        self.path_rows["p2_profile_path"] = PathConfigRow("p2_profile_path", add_enabled=False)
        profiles_layout.addRow("Player 2 Profile:", self.path_rows["p2_profile_path"])
        self.path_rows["mediacenter_profile_path"] = PathConfigRow("mediacenter_profile_path", add_enabled=False)
        profiles_layout.addRow("Media Center Profile:", self.path_rows["mediacenter_profile_path"])
        self.path_rows["multimonitor_gaming_path"] = PathConfigRow("multimonitor_gaming_path", add_enabled=False)
        profiles_layout.addRow("MM Gaming Config:", self.path_rows["multimonitor_gaming_path"])
        self.path_rows["multimonitor_media_path"] = PathConfigRow("multimonitor_media_path", add_enabled=False)
        profiles_layout.addRow("MM Media/Desktop Config:", self.path_rows["multimonitor_media_path"])

        # --- Sequences Group ---
        sequences_widget = QWidget()
        sequences_layout = QHBoxLayout(sequences_widget)

        # Launch Sequence
        launch_sequence_group = QGroupBox("")
        launch_sequence_layout = QVBoxLayout(launch_sequence_group)
        launch_title = QLabel("<b>Launch Order</b>")
        launch_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.launch_sequence_list = DragDropListWidget()
        self.reset_launch_btn = QPushButton("Reset")
        # keep 'Drag to reorder' label as-is (exception)
        launch_sequence_layout.addWidget(launch_title)
        launch_sequence_layout.addWidget(QLabel("Drag to reorder:"))
        launch_sequence_layout.addWidget(self.launch_sequence_list)
        launch_sequence_layout.addWidget(self.reset_launch_btn)
        sequences_layout.addWidget(launch_sequence_group)

        # Exit Sequence
        exit_sequence_group = QGroupBox("")
        exit_sequence_layout = QVBoxLayout(exit_sequence_group)
        exit_title = QLabel("<b>Exit Order</b>")
        exit_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.exit_sequence_list = DragDropListWidget()
        self.reset_exit_btn = QPushButton("Reset")
        exit_sequence_layout.addWidget(exit_title)
        exit_sequence_layout.addWidget(self.exit_sequence_list)
        exit_sequence_layout.addWidget(self.reset_exit_btn)
        sequences_layout.addWidget(exit_sequence_group)

        # --- Accordion Setup ---
        source_config_section = AccordionSection("Source Configuration", source_config_widget)
        directories_section = AccordionSection("Paths", directories_widget)
        applications_section = AccordionSection("Applications", applications_widget)
        profiles_section = AccordionSection("Profiles", profiles_widget)
        sequences_section = AccordionSection("Execution Sequences", sequences_widget)

        main_layout.addWidget(source_config_section)
        main_layout.addWidget(directories_section)
        main_layout.addWidget(applications_section)
        main_layout.addWidget(profiles_section)
        main_layout.addWidget(sequences_section)
        main_layout.addStretch()
        self._connect_signals()

    def _connect_signals(self):
        self.add_source_dir_button.clicked.connect(self._add_source_dir)
        self.remove_source_dir_button.clicked.connect(self._remove_source_dir)
        self.add_excluded_dir_button.clicked.connect(self._add_excluded_dir)
        self.remove_excluded_dir_button.clicked.connect(self._remove_excluded_dir)
        self.reset_launch_btn.clicked.connect(self._reset_launch_sequence)
        self.reset_exit_btn.clicked.connect(self._reset_exit_sequence)

        self.source_dirs_list.model().rowsMoved.connect(self.config_changed.emit)
        self.source_dirs_list.model().rowsInserted.connect(lambda: self.config_changed.emit())
        self.source_dirs_list.model().rowsRemoved.connect(self.config_changed.emit)
        self.excluded_dirs_list.model().rowsMoved.connect(self.config_changed.emit)
        self.excluded_dirs_list.model().rowsInserted.connect(lambda: self.config_changed.emit())
        self.excluded_dirs_list.model().rowsRemoved.connect(self.config_changed.emit)
        # Path rows
        for row in self.path_rows.values():
            row.valueChanged.connect(self.config_changed.emit)

        # Sequences
        self.launch_sequence_list.model().rowsMoved.connect(self.config_changed.emit)
        self.exit_sequence_list.model().rowsMoved.connect(self.config_changed.emit)

        # Logging
        self.logging_verbosity_combo.currentTextChanged.connect(self.main_window._on_logging_verbosity_changed)
        
        # Appearance
        self.font_combo.currentTextChanged.connect(self._on_appearance_changed)
        self.font_size_spin.valueChanged.connect(self._on_appearance_changed)
        self.theme_combo.currentTextChanged.connect(self._on_appearance_changed)
        self.restart_btn.clicked.connect(self._reset_to_defaults)

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