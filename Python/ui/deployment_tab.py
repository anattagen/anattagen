from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QPushButton, QCheckBox, QGroupBox, QMenu, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import pyqtSignal
from Python.ui.accordion import AccordionSection
from Python.models import AppConfig
import os


def get_module_path():
    """Dynamically calculates the path to the current module."""
    return os.path.dirname(os.path.abspath(__file__))


class DeploymentTab(QWidget):
    """A QWidget that encapsulates all UI and logic for the Deployment tab."""

    config_changed = pyqtSignal()
    index_sources_requested = pyqtSignal()
    create_selected_requested = pyqtSignal()
    download_steam_json_requested = pyqtSignal(int)
    delete_steam_json_requested = pyqtSignal()
    delete_steam_cache_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._populate_ui()

    def _populate_ui(self):
        """Create and arrange all widgets for the Deployment tab."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # --- General Options Section ---
        general_options_widget = QWidget()
        general_options_layout = QVBoxLayout(general_options_widget)

        # Row 1: Network check and Steam DB button
        self.net_check_checkbox = QCheckBox("Check Network Connection")
        steam_db_button = QPushButton("STEAM DB")
        steam_db_menu = QMenu(steam_db_button)
        download_v1_action = steam_db_menu.addAction("Download steam.json (v1)")
        download_v2_action = steam_db_menu.addAction("Download steam.json (v2)")
        steam_db_menu.addSeparator()
        delete_json_action = steam_db_menu.addAction("Delete steam.json")
        delete_cache_action = steam_db_menu.addAction("Delete Steam Caches")
        steam_db_button.setMenu(steam_db_menu)

        row1_layout = QHBoxLayout()
        row1_layout.addWidget(self.net_check_checkbox)
        row1_layout.addWidget(steam_db_button)
        row1_layout.addStretch(1)
        general_options_layout.addLayout(row1_layout)

        # Row 2: Hide Taskbar and Run As Admin
        self.hide_taskbar_checkbox = QCheckBox("Hide Taskbar")
        self.run_as_admin_checkbox = QCheckBox("Run As Admin")
        row2_layout = QHBoxLayout()
        row2_layout.addWidget(self.hide_taskbar_checkbox)
        row2_layout.addWidget(self.run_as_admin_checkbox)
        row2_layout.addStretch(1)
        general_options_layout.addLayout(row2_layout)

        # Row 3: Enable Steam Name Matching (moved from Setup Tab)
        self.name_check_checkbox = QCheckBox("Enable Steam Name Matching")
        self.name_check_checkbox.setToolTip("Attempt to match indexed games with Steam titles for better naming. Requires steam.json.")
        general_options_layout.addWidget(self.name_check_checkbox)

        # Row 4: Steam JSON Version (moved from Setup Tab)
        steam_version_layout = QHBoxLayout()
        steam_version_label = QLabel("Steam JSON Version:")
        self.steam_json_v1_radio = QRadioButton("v1")
        self.steam_json_v2_radio = QRadioButton("v2")
        self.steam_json_v2_radio.setChecked(True)
        self.steam_version_group = QButtonGroup(self)
        self.steam_version_group.addButton(self.steam_json_v1_radio)
        self.steam_version_group.addButton(self.steam_json_v2_radio)
        steam_version_layout.addWidget(steam_version_label)
        steam_version_layout.addWidget(self.steam_json_v1_radio)
        steam_version_layout.addWidget(self.steam_json_v2_radio)
        steam_version_layout.addStretch(1)
        general_options_layout.addLayout(steam_version_layout)

        # --- Creation Options Section ---
        creation_options_widget = QWidget()
        creation_options_layout = QVBoxLayout(creation_options_widget)
        
        self.create_profile_folders_checkbox = QCheckBox("Create Profile Folders")
        self.create_overwrite_launcher_checkbox = QCheckBox("Create/Overwrite Launcher")
        self.create_overwrite_joystick_profiles_checkbox = QCheckBox("Create/Overwrite Joystick Profiles")
        
        index_sources_button = QPushButton("Index Sources")
        create_button = QPushButton("Create Selected")
        create_button.setStyleSheet("QPushButton { font-weight: bold; background-color: #4CAF50; color: white; padding: 8px; }")

        creation_options_layout.addWidget(self.create_profile_folders_checkbox)
        creation_options_layout.addWidget(self.create_overwrite_launcher_checkbox)
        creation_options_layout.addWidget(self.create_overwrite_joystick_profiles_checkbox)
        creation_options_layout.addSpacing(10)
        creation_options_layout.addWidget(index_sources_button)
        creation_options_layout.addWidget(create_button)
        creation_options_layout.addStretch(1)

        # --- Accordion Setup ---
        general_options_section = AccordionSection("General Options", general_options_widget)
        creation_section = AccordionSection("Creation", creation_options_widget)

        main_layout.addWidget(general_options_section)
        main_layout.addWidget(creation_section)
        main_layout.addStretch(1)

        # --- Connect Signals ---
        self.net_check_checkbox.stateChanged.connect(self.config_changed.emit)
        self.hide_taskbar_checkbox.stateChanged.connect(self.config_changed.emit)
        self.run_as_admin_checkbox.stateChanged.connect(self.config_changed.emit)
        self.name_check_checkbox.stateChanged.connect(self.config_changed.emit)
        self.steam_json_v1_radio.toggled.connect(self.config_changed.emit)
        self.steam_json_v2_radio.toggled.connect(self.config_changed.emit)
        self.create_overwrite_launcher_checkbox.stateChanged.connect(self.config_changed.emit)
        self.create_profile_folders_checkbox.stateChanged.connect(self.config_changed.emit)
        self.create_overwrite_joystick_profiles_checkbox.stateChanged.connect(self.config_changed.emit)

        index_sources_button.clicked.connect(self.index_sources_requested.emit)
        create_button.clicked.connect(self.create_selected_requested.emit)
        download_v1_action.triggered.connect(lambda: self.download_steam_json_requested.emit(1))
        download_v2_action.triggered.connect(lambda: self.download_steam_json_requested.emit(2))
        delete_json_action.triggered.connect(self.delete_steam_json_requested.emit)
        delete_cache_action.triggered.connect(self.delete_steam_cache_requested.emit)

    def sync_ui_from_config(self, config: AppConfig):
        """Updates the UI widgets with values from the AppConfig model."""
        self.blockSignals(True)

        self.net_check_checkbox.setChecked(config.net_check)
        self.hide_taskbar_checkbox.setChecked(config.hide_taskbar)
        self.run_as_admin_checkbox.setChecked(config.run_as_admin)
        self.name_check_checkbox.setChecked(config.enable_name_matching)
        
        if config.steam_json_version == 1:
            self.steam_json_v1_radio.setChecked(True)
        else:
            self.steam_json_v2_radio.setChecked(True)

        self.create_profile_folders_checkbox.setChecked(config.create_profile_folders)
        self.create_overwrite_launcher_checkbox.setChecked(config.create_overwrite_launcher)
        self.create_overwrite_joystick_profiles_checkbox.setChecked(config.create_overwrite_joystick_profiles)

        self.blockSignals(False)

    def sync_config_from_ui(self, config: AppConfig):
        """Updates the AppConfig model with values from the UI widgets."""
        config.net_check = self.net_check_checkbox.isChecked()
        config.hide_taskbar = self.hide_taskbar_checkbox.isChecked()
        config.run_as_admin = self.run_as_admin_checkbox.isChecked()
        config.enable_name_matching = self.name_check_checkbox.isChecked()
        config.steam_json_version = 1 if self.steam_json_v1_radio.isChecked() else 2

        config.create_profile_folders = self.create_profile_folders_checkbox.isChecked()
        config.create_overwrite_launcher = self.create_overwrite_launcher_checkbox.isChecked()
        config.create_overwrite_joystick_profiles = self.create_overwrite_joystick_profiles_checkbox.isChecked()
