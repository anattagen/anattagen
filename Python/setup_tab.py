from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QLabel, QLineEdit, QFormLayout,
    QPushButton, QComboBox, QListWidget, QAbstractItemView, QHBoxLayout,
    QRadioButton, QFileDialog, QButtonGroup
)
from PyQt6.QtCore import pyqtSignal
from Python.models import AppConfig
from Python.ui.widgets import DragDropListWidget
from Python.ui.accordion import AccordionSection
import os
import re

def to_snake_case(name):
    """Convert a string to snake_case format"""
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'[\s-]+(?=[\w])', '_', name.strip()).lower()
    name = re.sub(r'\W', '', name)
    return name

class SetupTab(QWidget):
    """A QWidget that encapsulates all UI and logic for the Setup tab."""
    
    config_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.deployment_path_options = {}
        self._setup_ui()

    def _create_path_row_with_cen_lc(self, label_text, line_edit_attr, is_directory=False):
        """Helper to create a path row with CEN/LC radio buttons."""
        line_edit = QLineEdit()
        browse_button = QPushButton("Browse...")
        setattr(self, line_edit_attr, line_edit)

        cen_radio = QRadioButton("CEN")
        lc_radio = QRadioButton("LC")
        cen_radio.setChecked(True)
        button_group = QButtonGroup(self)
        button_group.addButton(cen_radio)
        button_group.addButton(lc_radio)

        field_layout = QHBoxLayout()
        field_layout.addWidget(line_edit)
        field_layout.addWidget(browse_button)
        field_layout.addWidget(cen_radio)
        field_layout.addWidget(lc_radio)

        if is_directory:
            browse_button.clicked.connect(lambda checked, le=line_edit: self._browse_for_directory(le))
        else:
            browse_button.clicked.connect(lambda checked, le=line_edit: self._browse_for_file(le))

        self.deployment_path_options[to_snake_case(label_text.replace(":", ""))] = button_group
        return field_layout

    def _setup_ui(self):
        """Create and arrange all widgets for the Setup tab."""
        main_layout = QVBoxLayout(self)
        
        # --- Main Settings Group ---
        main_settings_group = QGroupBox("Main Settings")
        main_settings_layout = QFormLayout()

        # Source Directories
        self.source_dirs_list = QListWidget()
        self.source_dirs_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        source_buttons_layout = QHBoxLayout()
        self.add_source_dir_button = QPushButton("Add...")
        self.remove_source_dir_button = QPushButton("Remove")
        source_buttons_layout.addWidget(self.add_source_dir_button)
        source_buttons_layout.addWidget(self.remove_source_dir_button)
        main_settings_layout.addRow("Source Directories:", self.source_dirs_list)
        main_settings_layout.addRow("", source_buttons_layout)

        # Profiles Directory with CEN/LC
        profiles_layout = self._create_path_row_with_cen_lc("Profiles Directory:", "profiles_dir_edit", is_directory=True)
        main_settings_layout.addRow("Profiles Directory:", profiles_layout)

        # Launchers Directory with CEN/LC
        launchers_layout = self._create_path_row_with_cen_lc("Launchers Directory:", "launchers_dir_edit", is_directory=True)
        main_settings_layout.addRow("Launchers Directory:", launchers_layout)

        # Logging Verbosity
        self.logging_verbosity_combo = QComboBox()
        self.logging_verbosity_combo.addItems(["None", "Low", "Medium", "High"])
        main_settings_layout.addRow("Logging Verbosity:", self.logging_verbosity_combo)

        main_settings_group.setLayout(main_settings_layout)

        # --- Application & Element Paths Group ---
        paths_group = QGroupBox("Application & Element Paths")
        paths_layout = QFormLayout()

        # Application paths
        paths_layout.addRow("Controller Mapper:", self._create_path_row_with_cen_lc("Controller Mapper:", "controller_mapper_app_edit"))
        paths_layout.addRow("Borderless Windowing:", self._create_path_row_with_cen_lc("Borderless Windowing:", "borderless_app_edit"))
        paths_layout.addRow("Multi-Monitor App:", self._create_path_row_with_cen_lc("Multi-Monitor App:", "multimonitor_app_edit"))
        
        # Profile paths
        paths_layout.addRow("P1 Profile:", self._create_path_row_with_cen_lc("P1 Profile:", "p1_profile_edit"))
        paths_layout.addRow("P2 Profile:", self._create_path_row_with_cen_lc("P2 Profile:", "p2_profile_edit"))
        paths_layout.addRow("Mediacenter Profile:", self._create_path_row_with_cen_lc("Mediacenter Profile:", "mediacenter_profile_edit"))
        paths_layout.addRow("MM Gaming Config:", self._create_path_row_with_cen_lc("MM Gaming Config:", "multimonitor_gaming_config_edit"))
        paths_layout.addRow("MM Media Config:", self._create_path_row_with_cen_lc("MM Media Config:", "multimonitor_media_config_edit"))

        # Pre-launch apps
        paths_layout.addRow("Pre 1:", self._create_path_row_with_cen_lc("Pre 1:", "pre1_edit"))
        paths_layout.addRow("Pre 2:", self._create_path_row_with_cen_lc("Pre 2:", "pre2_edit"))
        paths_layout.addRow("Pre 3:", self._create_path_row_with_cen_lc("Pre 3:", "pre3_edit"))

        # Post-launch apps
        paths_layout.addRow("Post 1:", self._create_path_row_with_cen_lc("Post 1:", "post1_edit"))
        paths_layout.addRow("Post 2:", self._create_path_row_with_cen_lc("Post 2:", "post2_edit"))
        paths_layout.addRow("Post 3:", self._create_path_row_with_cen_lc("Post 3:", "post3_edit"))

        # Just Before/After apps
        paths_layout.addRow("Just After Launch:", self._create_path_row_with_cen_lc("Just After Launch:", "just_after_launch_edit"))
        paths_layout.addRow("Just Before Exit:", self._create_path_row_with_cen_lc("Just Before Exit:", "just_before_exit_edit"))

        paths_group.setLayout(paths_layout)

        # --- Sequences Group ---
        sequences_widget = QWidget()
        sequences_layout = QHBoxLayout(sequences_widget)

        # Launch Sequence
        launch_sequence_group = QGroupBox("Launch Sequence")
        launch_sequence_layout = QVBoxLayout(launch_sequence_group)
        self.launch_sequence_list = DragDropListWidget()
        self.reset_launch_btn = QPushButton("Reset")
        launch_sequence_layout.addWidget(QLabel("Drag to reorder:"))
        launch_sequence_layout.addWidget(self.launch_sequence_list)
        launch_sequence_layout.addWidget(self.reset_launch_btn)
        sequences_layout.addWidget(launch_sequence_group)

        # Exit Sequence
        exit_sequence_group = QGroupBox("Exit Sequence")
        exit_sequence_layout = QVBoxLayout(exit_sequence_group)
        self.exit_sequence_list = DragDropListWidget()
        self.reset_exit_btn = QPushButton("Reset")
        exit_sequence_layout.addWidget(QLabel("Drag to reorder:"))
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
        self.reset_launch_btn.clicked.connect(self._reset_launch_sequence)
        self.reset_exit_btn.clicked.connect(self._reset_exit_sequence)

        self.source_dirs_list.model().rowsMoved.connect(self.config_changed.emit)
        self.source_dirs_list.model().dataChanged.connect(self.config_changed.emit)

        # Path edits
        path_attrs = [
            "profiles_dir_edit", "launchers_dir_edit", "controller_mapper_app_edit",
            "borderless_app_edit", "multimonitor_app_edit", "p1_profile_edit",
            "p2_profile_edit", "mediacenter_profile_edit", "multimonitor_gaming_config_edit",
            "multimonitor_media_config_edit", "pre1_edit", "pre2_edit", "pre3_edit",
            "post1_edit", "post2_edit", "post3_edit", "just_after_launch_edit", "just_before_exit_edit"
        ]
        for attr in path_attrs:
            getattr(self, attr).textChanged.connect(self.config_changed.emit)

        # CEN/LC radio buttons
        for group in self.deployment_path_options.values():
            group.buttonClicked.connect(self.config_changed.emit)

        # Sequences
        self.launch_sequence_list.model().rowsMoved.connect(self.config_changed.emit)
        self.exit_sequence_list.model().rowsMoved.connect(self.config_changed.emit)

        # Logging
        self.logging_verbosity_combo.currentTextChanged.connect(self.config_changed.emit)

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

    def _browse_for_directory(self, line_edit: QLineEdit):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory", line_edit.text())
        if directory:
            line_edit.setText(directory)
            self.config_changed.emit()
            
    def _browse_for_file(self, line_edit: QLineEdit):
        file, _ = QFileDialog.getOpenFileName(self, "Select File", line_edit.text())
        if file:
            line_edit.setText(file)
            self.config_changed.emit()

    def _reset_launch_sequence(self):
        self.launch_sequence_list.clear()
        self.launch_sequence_list.addItems(["Controller-Mapper", "Monitor-Config", "No-TB", "Pre1", "Pre2", "Pre3", "Borderless"])
        self.config_changed.emit()

    def _reset_exit_sequence(self):
        self.exit_sequence_list.clear()
        self.exit_sequence_list.addItems(["Post1", "Post2", "Post3", "Monitor-Config", "Taskbar", "Controller-Mapper"])
        self.config_changed.emit()

    def sync_ui_from_config(self, config: AppConfig):
        self.blockSignals(True)

        self.source_dirs_list.clear()
        self.source_dirs_list.addItems(config.source_dirs)
        self.logging_verbosity_combo.setCurrentText(config.logging_verbosity)

        self.profiles_dir_edit.setText(config.profiles_dir)
        self.launchers_dir_edit.setText(config.launchers_dir)
        self.controller_mapper_app_edit.setText(config.controller_mapper_path)
        self.borderless_app_edit.setText(config.borderless_gaming_path)
        self.multimonitor_app_edit.setText(config.multi_monitor_tool_path)
        self.p1_profile_edit.setText(config.p1_profile_path)
        self.p2_profile_edit.setText(config.p2_profile_path)
        self.mediacenter_profile_edit.setText(config.mediacenter_profile_path)
        self.multimonitor_gaming_config_edit.setText(config.multimonitor_gaming_path)
        self.multimonitor_media_config_edit.setText(config.multimonitor_media_path)
        self.pre1_edit.setText(config.pre1_path)
        self.pre2_edit.setText(config.pre2_path)
        self.pre3_edit.setText(config.pre3_path)
        self.post1_edit.setText(config.post1_path)
        self.post2_edit.setText(config.post2_path)
        self.post3_edit.setText(config.post3_path)
        self.just_after_launch_edit.setText(config.just_after_launch_path)
        self.just_before_exit_edit.setText(config.just_before_exit_path)

        for key, group in self.deployment_path_options.items():
            mode = config.deployment_path_modes.get(key, "CEN")
            for button in group.buttons():
                if button.text() == mode:
                    button.setChecked(True)
                    break

        self.launch_sequence_list.clear()
        self.launch_sequence_list.addItems(config.launch_sequence if config.launch_sequence else 
            ["Controller-Mapper", "Monitor-Config", "No-TB", "Pre1", "Pre2", "Pre3", "Borderless"])
        self.exit_sequence_list.clear()
        self.exit_sequence_list.addItems(config.exit_sequence if config.exit_sequence else
            ["Post1", "Post2", "Post3", "Monitor-Config", "Taskbar", "Controller-Mapper"])

        self.blockSignals(False)

    def sync_config_from_ui(self, config: AppConfig):
        config.source_dirs = [self.source_dirs_list.item(i).text() for i in range(self.source_dirs_list.count())]
        config.logging_verbosity = self.logging_verbosity_combo.currentText()

        config.profiles_dir = self.profiles_dir_edit.text()
        config.launchers_dir = self.launchers_dir_edit.text()
        config.controller_mapper_path = self.controller_mapper_app_edit.text()
        config.borderless_gaming_path = self.borderless_app_edit.text()
        config.multi_monitor_tool_path = self.multimonitor_app_edit.text()
        config.p1_profile_path = self.p1_profile_edit.text()
        config.p2_profile_path = self.p2_profile_edit.text()
        config.mediacenter_profile_path = self.mediacenter_profile_edit.text()
        config.multimonitor_gaming_path = self.multimonitor_gaming_config_edit.text()
        config.multimonitor_media_path = self.multimonitor_media_config_edit.text()
        config.pre1_path = self.pre1_edit.text()
        config.pre2_path = self.pre2_edit.text()
        config.pre3_path = self.pre3_edit.text()
        config.post1_path = self.post1_edit.text()
        config.post2_path = self.post2_edit.text()
        config.post3_path = self.post3_edit.text()
        config.just_after_launch_path = self.just_after_launch_edit.text()
        config.just_before_exit_path = self.just_before_exit_edit.text()

        for key, group in self.deployment_path_options.items():
            checked_button = group.checkedButton()
            if checked_button:
                config.deployment_path_modes[key] = checked_button.text()

        config.launch_sequence = [self.launch_sequence_list.item(i).text() for i in range(self.launch_sequence_list.count())]
        config.exit_sequence = [self.exit_sequence_list.item(i).text() for i in range(self.exit_sequence_list.count())]
