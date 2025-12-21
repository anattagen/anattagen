import os
import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QLabel, QLineEdit, QFormLayout,
    QPushButton, QComboBox, QListWidget, QAbstractItemView, QHBoxLayout, QCheckBox,
    QRadioButton, QFileDialog, QButtonGroup, QApplication, QStyleFactory, QSpinBox, QFrame
)
from PyQt6.QtGui import QFontDatabase, QFont
from PyQt6.QtCore import pyqtSignal, Qt
from Python.models import AppConfig
from Python.ui.widgets import DragDropListWidget
from Python.ui.accordion import AccordionSection

class PathConfigRow(QWidget):
    """Custom widget for a path configuration row with options."""
    
    valueChanged = pyqtSignal()

    def __init__(self, config_key, is_directory=False, add_enabled=True, add_run_wait=False, parent=None):
        super().__init__(parent)
        self.config_key = config_key
        self.is_directory = is_directory
        self.add_enabled = add_enabled
        self.add_run_wait = add_run_wait
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Enabled Checkbox
        if self.add_enabled:
            self.enabled_cb = QCheckBox()
            self.enabled_cb.setChecked(True)
            self.enabled_cb.stateChanged.connect(self.valueChanged.emit)
            layout.addWidget(self.enabled_cb)
        else:
            spacer = QWidget()
            spacer.setFixedWidth(20)
            layout.addWidget(spacer)
            self.enabled_cb = None

        # Line Edit
        self.line_edit = QLineEdit()
        self.line_edit.textChanged.connect(self.valueChanged.emit)
        layout.addWidget(self.line_edit)

        # Browse Button
        self.browse_btn = QPushButton(". . .")
        self.browse_btn.setFixedWidth(40)
        self.browse_btn.clicked.connect(self._on_browse)
        layout.addWidget(self.browse_btn)

        # Radio Buttons
        self.cen_radio = QRadioButton("CEN")
        self.lc_radio = QRadioButton("LC")
        self.cen_radio.setChecked(True)
        self.mode_group = QButtonGroup(self)
        self.mode_group.addButton(self.cen_radio)
        self.mode_group.addButton(self.lc_radio)
        self.mode_group.buttonClicked.connect(self.valueChanged.emit)
        layout.addWidget(self.cen_radio)
        layout.addWidget(self.lc_radio)

        # Run Wait Checkbox
        if self.add_run_wait:
            self.run_wait_cb = QCheckBox("Wait")
            self.run_wait_cb.stateChanged.connect(self.valueChanged.emit)
            layout.addWidget(self.run_wait_cb)
        else:
            self.run_wait_cb = None

    def _on_browse(self):
        current_path = self.line_edit.text()
        if self.is_directory:
            directory = QFileDialog.getExistingDirectory(self, "Select Directory", current_path)
            if directory:
                self.line_edit.setText(directory)
        else:
            file, _ = QFileDialog.getOpenFileName(self, "Select File", current_path)
            if file:
                self.line_edit.setText(file)

    @property
    def path(self):
        return self.line_edit.text()

    @path.setter
    def path(self, value):
        self.line_edit.setText(value)

    @property
    def mode(self):
        return "LC" if self.lc_radio.isChecked() else "CEN"

    @mode.setter
    def mode(self, value):
        if value == "LC":
            self.lc_radio.setChecked(True)
        else:
            self.cen_radio.setChecked(True)

    @property
    def enabled(self):
        return self.enabled_cb.isChecked() if self.enabled_cb else True

    @enabled.setter
    def enabled(self, value):
        if self.enabled_cb:
            self.enabled_cb.setChecked(value)

    @property
    def run_wait(self):
        return self.run_wait_cb.isChecked() if self.run_wait_cb else False

    @run_wait.setter
    def run_wait(self, value):
        if self.run_wait_cb:
            self.run_wait_cb.setChecked(value)

class SetupTab(QWidget):
    """A QWidget that encapsulates all UI and logic for the Setup tab."""
    
    config_changed = pyqtSignal()

    PATH_MAPPINGS = {
        "profiles_directory": "profiles_dir",
        "launchers_directory": "launchers_dir",
        "controller_mapper": "controller_mapper_path",
        "p1_profile": "p1_profile_path",
        "p2_profile": "p2_profile_path",
        "mediacenter_profile": "mediacenter_profile_path",
        "multi_monitor_app": "multi_monitor_tool_path",
        "mm_gaming_config": "multimonitor_gaming_path",
        "mm_media_config": "multimonitor_media_path",
        "borderless_windowing": "borderless_gaming_path",
        "pre_1": "pre1_path",
        "pre_2": "pre2_path",
        "pre_3": "pre3_path",
        "just_after_launch": "just_after_launch_path",
        "just_before_exit": "just_before_exit_path",
        "post_1": "post1_path",
        "post_2": "post2_path",
        "post_3": "post3_path",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.path_rows = {}
        self._setup_ui()

    def _setup_ui(self):
        """Create and arrange all widgets for the Setup tab."""
        main_layout = QVBoxLayout(self)
        
        # --- Main Settings Group ---
        main_settings_group = QGroupBox("Main Settings")
        main_settings_layout = QFormLayout()

        # Sources
        self.source_dirs_list = QListWidget()
        self.source_dirs_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.source_dirs_list.setMaximumHeight(100)
        source_buttons_layout = QHBoxLayout()
        self.add_source_dir_button = QPushButton("Add...")
        self.remove_source_dir_button = QPushButton("Remove")
        source_buttons_layout.addWidget(self.add_source_dir_button)
        source_buttons_layout.addWidget(self.remove_source_dir_button)
        main_settings_layout.addRow("Sources:", self.source_dirs_list)
        main_settings_layout.addRow("", source_buttons_layout)

        # Excluded Items
        self.excluded_dirs_list = QListWidget()
        self.excluded_dirs_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.excluded_dirs_list.setMaximumHeight(100)
        excluded_buttons_layout = QHBoxLayout()
        self.add_excluded_dir_button = QPushButton("+")
        self.add_excluded_dir_button.setFixedWidth(30)
        self.remove_excluded_dir_button = QPushButton("x")
        self.remove_excluded_dir_button.setFixedWidth(30)
        excluded_buttons_layout.addStretch(1)
        excluded_buttons_layout.addWidget(self.add_excluded_dir_button)
        excluded_buttons_layout.addWidget(self.remove_excluded_dir_button)
        excluded_label = QLabel("Excluded Items:")
        excluded_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        main_settings_layout.addRow(excluded_label, self.excluded_dirs_list)
        main_settings_layout.addRow("", excluded_buttons_layout)

        # Profiles with CEN/LC
        self.path_rows["profiles_directory"] = PathConfigRow("profiles_directory", is_directory=True, add_enabled=False)
        main_settings_layout.addRow("Profiles:", self.path_rows["profiles_directory"])

        # Launchers with CEN/LC
        self.path_rows["launchers_directory"] = PathConfigRow("launchers_directory", is_directory=True, add_enabled=False)
        main_settings_layout.addRow("Launchers:", self.path_rows["launchers_directory"])

        # Logging Verbosity
        self.logging_verbosity_combo = QComboBox()
        self.logging_verbosity_combo.addItems(["None", "Low", "Medium", "High"])

        # Font Dropdown
        self.font_combo = QComboBox()
        self.font_combo.addItem("System")
        # Try to find site folder
        site_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "site")
        if not os.path.exists(site_path):
            site_path = os.path.join(os.path.dirname(__file__), "site")
        if os.path.exists(site_path):
            for f in os.listdir(site_path):
                if f.lower().endswith((".ttf", ".otf")):
                    self.font_combo.addItem(f)

        # Font Size SpinBox
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(10)
        self.font_size_spin.valueChanged.connect(self._on_appearance_changed)

        # Theme Dropdown
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Default", "Windows", "Vista", "MacOS", "Fusion", "Dark", "Light"])

        # Restart Button
        self.restart_btn = QPushButton("*")
        self.restart_btn.setToolTip("Reset application configuration to defaults")
        self.restart_btn.setFixedWidth(25)

        appearance_layout = QHBoxLayout()
        appearance_layout.addWidget(self.logging_verbosity_combo)
        appearance_layout.addStretch()

        # set object names for persistence
        self.logging_verbosity_combo.setObjectName("logging_verbosity_combo")
        self.font_combo.setObjectName("font_combo")
        self.theme_combo.setObjectName("theme_combo")
        self.font_size_spin.setObjectName("font_size_spin")
        self.restart_btn.setObjectName("restart_btn")

        main_settings_layout.addRow("Log/Reset:", appearance_layout)

        # Theme options (right aligned / upper-right)
        theme_layout = QHBoxLayout()
        theme_layout.addStretch()
        theme_layout.addWidget(QLabel("Font:"))
        theme_layout.addWidget(self.font_combo)
        theme_layout.addWidget(QLabel("Size:"))
        theme_layout.addWidget(self.font_size_spin)
        theme_layout.addWidget(QLabel("Theme:"))
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addWidget(self.restart_btn)
        main_settings_layout.addRow("", theme_layout)

        main_settings_group.setLayout(main_settings_layout)

        # --- Application & Element Paths Group ---
        paths_group = QGroupBox("Application & Element Paths")
        paths_layout = QFormLayout()

        # Application paths
        self.path_rows["controller_mapper"] = PathConfigRow("controller_mapper", add_run_wait=True)
        mapper_label = QLabel("<b>Mapper:</b>")
        paths_layout.addRow(mapper_label, self.path_rows["controller_mapper"])
        self.path_rows["p1_profile"] = PathConfigRow("p1_profile", add_enabled=False)
        p1_label = QLabel("Player 1 Profile:")
        p1_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        paths_layout.addRow(p1_label, self.path_rows["p1_profile"])
        self.path_rows["p2_profile"] = PathConfigRow("p2_profile", add_enabled=False)
        p2_label = QLabel("Player 2 Profile:")
        p2_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        paths_layout.addRow(p2_label, self.path_rows["p2_profile"])
        self.path_rows["mediacenter_profile"] = PathConfigRow("mediacenter_profile", add_enabled=False)
        mediacenter_label = QLabel("Media Center Profile:")
        mediacenter_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        paths_layout.addRow(mediacenter_label, self.path_rows["mediacenter_profile"])
        
        # Add divider line
        divider1 = QFrame()
        divider1.setFrameShape(QFrame.Shape.HLine)
        divider1.setFrameShadow(QFrame.Shadow.Sunken)
        paths_layout.addRow(divider1)
        
        self.path_rows["multi_monitor_app"] = PathConfigRow("multi_monitor_app", add_run_wait=True)
        mm_app_label = QLabel("<b>Multi-Monitor App:</b>")
        paths_layout.addRow(mm_app_label, self.path_rows["multi_monitor_app"])
        self.path_rows["mm_gaming_config"] = PathConfigRow("mm_gaming_config", add_enabled=False)
        game_display_label = QLabel("Game Display:")
        game_display_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        paths_layout.addRow(game_display_label, self.path_rows["mm_gaming_config"])
        self.path_rows["mm_media_config"] = PathConfigRow("mm_media_config", add_enabled=False)
        desktop_display_label = QLabel("Desktop Display:")
        desktop_display_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        paths_layout.addRow(desktop_display_label, self.path_rows["mm_media_config"])
        
        # Add divider line
        divider2 = QFrame()
        divider2.setFrameShape(QFrame.Shape.HLine)
        divider2.setFrameShadow(QFrame.Shadow.Sunken)
        paths_layout.addRow(divider2)
        
        self.path_rows["borderless_windowing"] = PathConfigRow("borderless_windowing", add_run_wait=True)
        windowing_label = QLabel("<b>Windowing:</b>")
        windowing_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        paths_layout.addRow(windowing_label, self.path_rows["borderless_windowing"])
        # Divider after Windowing
        div_w = QFrame()
        div_w.setFrameShape(QFrame.Shape.HLine)
        div_w.setFrameShadow(QFrame.Shadow.Sunken)
        paths_layout.addRow(div_w)
        
        # Profile paths

        # Pre-launch apps
        self.path_rows["pre_1"] = PathConfigRow("pre_1", add_run_wait=True)
        pre1_label = QLabel("<b>Pre 1:</b>")
        pre1_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        paths_layout.addRow(pre1_label, self.path_rows["pre_1"])
        div_pre1 = QFrame()
        div_pre1.setFrameShape(QFrame.Shape.HLine)
        div_pre1.setFrameShadow(QFrame.Shadow.Sunken)
        paths_layout.addRow(div_pre1)
        self.path_rows["pre_2"] = PathConfigRow("pre_2", add_run_wait=True)
        pre2_label = QLabel("<b>Pre 2:</b>")
        pre2_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        paths_layout.addRow(pre2_label, self.path_rows["pre_2"])
        div_pre2 = QFrame()
        div_pre2.setFrameShape(QFrame.Shape.HLine)
        div_pre2.setFrameShadow(QFrame.Shadow.Sunken)
        paths_layout.addRow(div_pre2)
        self.path_rows["pre_3"] = PathConfigRow("pre_3", add_run_wait=True)
        pre3_label = QLabel("<b>Pre 3:</b>")
        pre3_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        paths_layout.addRow(pre3_label, self.path_rows["pre_3"])
        div_pre3 = QFrame()
        div_pre3.setFrameShape(QFrame.Shape.HLine)
        div_pre3.setFrameShadow(QFrame.Shadow.Sunken)
        paths_layout.addRow(div_pre3)
        # Just After app
        self.path_rows["just_after_launch"] = PathConfigRow("just_after_launch", add_run_wait=True)
        after_label = QLabel("<b>Just After Launch:</b>")
        after_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        paths_layout.addRow(after_label, self.path_rows["just_after_launch"])
        div_after = QFrame()
        div_after.setFrameShape(QFrame.Shape.HLine)
        div_after.setFrameShadow(QFrame.Shadow.Sunken)
        paths_layout.addRow(div_after)

        # Just Before app
        self.path_rows["just_before_exit"] = PathConfigRow("just_before_exit", add_run_wait=True)
        before_label = QLabel("<b>Just Before Exit:</b>")
        before_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        paths_layout.addRow(before_label, self.path_rows["just_before_exit"])
        div_before = QFrame()
        div_before.setFrameShape(QFrame.Shape.HLine)
        div_before.setFrameShadow(QFrame.Shadow.Sunken)
        paths_layout.addRow(div_before)
        # Post-launch apps
        self.path_rows["post_1"] = PathConfigRow("post_1", add_run_wait=True)
        post1_label = QLabel("<b>Post 1:</b>")
        post1_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        paths_layout.addRow(post1_label, self.path_rows["post_1"])
        div_post1 = QFrame()
        div_post1.setFrameShape(QFrame.Shape.HLine)
        div_post1.setFrameShadow(QFrame.Shadow.Sunken)
        paths_layout.addRow(div_post1)
        self.path_rows["post_2"] = PathConfigRow("post_2", add_run_wait=True)
        post2_label = QLabel("<b>Post 2:</b>")
        post2_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        paths_layout.addRow(post2_label, self.path_rows["post_2"])
        div_post2 = QFrame()
        div_post2.setFrameShape(QFrame.Shape.HLine)
        div_post2.setFrameShadow(QFrame.Shadow.Sunken)
        paths_layout.addRow(div_post2)
        self.path_rows["post_3"] = PathConfigRow("post_3", add_run_wait=True)
        post3_label = QLabel("<b>Post 3:</b>")
        post3_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        paths_layout.addRow(post3_label, self.path_rows["post_3"])


        paths_group.setLayout(paths_layout)

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
        main_settings_section = AccordionSection("Main Settings", main_settings_group)
        paths_section = AccordionSection("Application & Element Paths", paths_group)
        sequences_section = AccordionSection("Execution Sequences", sequences_widget)

        for section in [main_settings_section, paths_section, sequences_section]:
            main_layout.addWidget(section)

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
        self.source_dirs_list.model().dataChanged.connect(self.config_changed.emit)
        self.excluded_dirs_list.model().rowsMoved.connect(self.config_changed.emit)
        self.excluded_dirs_list.model().dataChanged.connect(self.config_changed.emit)

        # Path rows
        for row in self.path_rows.values():
            row.valueChanged.connect(self.config_changed.emit)

        # Sequences
        self.launch_sequence_list.model().rowsMoved.connect(self.config_changed.emit)
        self.exit_sequence_list.model().rowsMoved.connect(self.config_changed.emit)

        # Logging
        self.logging_verbosity_combo.currentTextChanged.connect(self.config_changed.emit)
        self.font_combo.currentTextChanged.connect(self._on_appearance_changed)
        self.theme_combo.currentTextChanged.connect(self._on_appearance_changed)
        self.restart_btn.clicked.connect(self._reset_to_defaults)

    def _reset_to_defaults(self):
        """Reset the application's configuration to the shipped defaults."""
        from PyQt6.QtWidgets import QMessageBox
        from Python.ui.config_manager import load_default_config

        reply = QMessageBox.question(self, "Reset to Defaults",
                                     "This will reset all configuration to the application's default values. Continue?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return

        # load_default_config expects the main_window object; pass the top-level window
        success = load_default_config(self.window())
        if success:
            # Notify user and emit change so other UI can refresh
            QMessageBox.information(self, "Defaults Loaded", "Default configuration has been loaded.")
            self.config_changed.emit()
        else:
            QMessageBox.warning(self, "Reset Failed", "Failed to load default configuration.")

    def _add_source_dir(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Source Directory")
        if directory:
            self.source_dirs_list.addItem(directory)
            self.config_changed.emit()

    def _remove_source_dir(self):
        selected_items = self.source_dirs_list.selectedItems()
        if not selected_items:
            return
        for item in selected_items:
            self.source_dirs_list.takeItem(self.source_dirs_list.row(item))
        self.config_changed.emit()

    def _add_excluded_dir(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory to Exclude")
        if directory:
            self.excluded_dirs_list.addItem(directory)
            self.config_changed.emit()

    def _remove_excluded_dir(self):
        selected_items = self.excluded_dirs_list.selectedItems()
        if not selected_items:
            return
        for item in selected_items:
            self.excluded_dirs_list.takeItem(self.excluded_dirs_list.row(item))
        self.config_changed.emit()

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
        
        # Apply Theme
        theme = self.theme_combo.currentText()
        if theme in QStyleFactory.keys():
            QApplication.setStyle(theme)
        elif theme == "Vista" and "WindowsVista" in QStyleFactory.keys():
            QApplication.setStyle("WindowsVista")
        elif theme == "MacOS" and "Macintosh" in QStyleFactory.keys():
            QApplication.setStyle("Macintosh")

        # Apply Font
        font_name = self.font_combo.currentText()
        font_size = self.font_size_spin.value()
        if font_name != "System":
            # Locate site folder
            site_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "site")
            if not os.path.exists(site_path):
                site_path = os.path.join(os.path.dirname(__file__), "site")
            
            font_path = os.path.join(site_path, font_name)
            if os.path.exists(font_path):
                font_id = QFontDatabase.addApplicationFont(font_path)
                if font_id != -1:
                    families = QFontDatabase.applicationFontFamilies(font_id)
                    if families:
                        font = QFont(families[0])
                        font.setPointSize(font_size)
                        QApplication.setFont(font)
        else:
            font = QApplication.font()
            font.setPointSize(font_size)
            QApplication.setFont(font)

    def _restart_app(self):
        QApplication.quit()
        os.execl(sys.executable, sys.executable, *sys.argv)

    def sync_ui_from_config(self, config: AppConfig):
        self.blockSignals(True)

        self.source_dirs_list.clear()
        self.source_dirs_list.addItems(config.source_dirs)
        self.excluded_dirs_list.clear()
        self.excluded_dirs_list.addItems(config.excluded_dirs)
        self.logging_verbosity_combo.setCurrentText(config.logging_verbosity)
        self.font_combo.setCurrentText(config.app_font)
        self.theme_combo.setCurrentText(config.app_theme)
        self.font_size_spin.setValue(config.font_size)

        for key, row in self.path_rows.items():
            if key in self.PATH_MAPPINGS:
                attr_name = self.PATH_MAPPINGS[key]
                if hasattr(config, attr_name):
                    row.path = getattr(config, attr_name)
            
            row.mode = config.deployment_path_modes.get(key, "CEN")
            row.enabled = config.defaults.get(f"{key}_enabled", True)
            row.run_wait = config.run_wait_states.get(f"{key}_run_wait", False)

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
        config.logging_verbosity = self.logging_verbosity_combo.currentText()
        config.app_font = self.font_combo.currentText()
        config.app_theme = self.theme_combo.currentText()
        config.font_size = self.font_size_spin.value()

        for key, attr_name in self.PATH_MAPPINGS.items():
            if key in self.path_rows:
                setattr(config, attr_name, self.path_rows[key].path)

        for key, row in self.path_rows.items():
            config.deployment_path_modes[key] = row.mode
            config.defaults[f"{key}_enabled"] = row.enabled
            config.run_wait_states[f"{key}_run_wait"] = row.run_wait

        config.launch_sequence = [self.launch_sequence_list.item(i).text() for i in range(self.launch_sequence_list.count())]
        config.exit_sequence = [self.exit_sequence_list.item(i).text() for i in range(self.exit_sequence_list.count())]
