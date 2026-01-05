from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QScrollArea,
    QPushButton, QCheckBox, QGroupBox, QMenu, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import pyqtSignal, Qt
from Python.ui.accordion import AccordionSection
from Python.models import AppConfig
import os


def get_module_path():
    """Dynamically calculates the path to the current module."""
    return os.path.dirname(os.path.abspath(__file__))


PATH_KEYS = [
    "profiles_dir", "launchers_dir",
    "controller_mapper_path", "borderless_gaming_path", "multi_monitor_tool_path",
    "just_after_launch_path", "just_before_exit_path",
    "p1_profile_path", "p2_profile_path", "mediacenter_profile_path",
    "multimonitor_gaming_path", "multimonitor_media_path",
    "pre1_path", "pre2_path", "pre3_path",
    "post1_path", "post2_path", "post3_path"
]

PATH_LABELS = {
    "profiles_dir": "Overwrite Profile Folders",
    "launchers_dir": "Overwrite Launcher",
    "controller_mapper_path": "Overwrite Controller Mapper",
    "borderless_gaming_path": "Overwrite Borderless Windowing",
    "multi_monitor_tool_path": "Overwrite Multi-Monitor Tool",
    "just_after_launch_path": "Overwrite Just After Launch",
    "just_before_exit_path": "Overwrite Just Before Exit",
    "p1_profile_path": "Overwrite Player 1 Profile",
    "p2_profile_path": "Overwrite Player 2 Profile",
    "mediacenter_profile_path": "Overwrite Media Center Profile",
    "multimonitor_gaming_path": "Overwrite MM Gaming Config",
    "multimonitor_media_path": "Overwrite MM Media Config",
    "pre1_path": "Overwrite Pre-Launch App 1",
    "pre2_path": "Overwrite Pre-Launch App 2",
    "pre3_path": "Overwrite Pre-Launch App 3",
    "post1_path": "Overwrite Post-Launch App 1",
    "post2_path": "Overwrite Post-Launch App 2",
    "post3_path": "Overwrite Post-Launch App 3"
}

class DeploymentTab(QWidget):
    """A QWidget that encapsulates all UI and logic for the Deployment tab."""

    config_changed = pyqtSignal()
    index_sources_requested = pyqtSignal()
    create_selected_requested = pyqtSignal()
    download_steam_json_requested = pyqtSignal(int)
    delete_steam_json_requested = pyqtSignal()
    delete_steam_cache_requested = pyqtSignal()
    process_steam_json_requested = pyqtSignal()
    
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.overwrite_checkboxes = {}
        self._populate_ui()

    def _populate_ui(self):
        """Create and arrange all widgets for the Deployment tab."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # --- General Options Section ---
        general_options_widget = QWidget()
        general_options_layout = QVBoxLayout(general_options_widget)

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

        # Add a single download button
        self.download_steam_json_button = QPushButton("Download")
        self.download_steam_json_button.setToolTip("Download the selected version of steam.json")
        steam_version_layout.addWidget(self.download_steam_json_button)

        steam_version_layout.addStretch(1)
        general_options_layout.addLayout(steam_version_layout)

        # Row 5: Steam Data Management Buttons
        steam_data_buttons_layout = QHBoxLayout()
        self.delete_json_button = QPushButton("Delete steam.json")
        self.delete_cache_button = QPushButton("Delete Steam Caches")
        self.process_json_button = QPushButton("Process Json")

        steam_data_buttons_layout.addWidget(self.process_json_button)
        steam_data_buttons_layout.addStretch(1)
        steam_data_buttons_layout.addWidget(self.delete_json_button)
        steam_data_buttons_layout.addWidget(self.delete_cache_button)
        general_options_layout.addSpacing(10)
        general_options_layout.addLayout(steam_data_buttons_layout)

        # --- Creation Options Section ---
        creation_options_widget = QWidget()
        creation_options_layout = QVBoxLayout(creation_options_widget)
        
        self.hide_taskbar_checkbox = QCheckBox("Hide Taskbar")
        self.hide_taskbar_checkbox.setChecked(False)
        self.run_as_admin_checkbox = QCheckBox("Run As Admin")
        self.run_as_admin_checkbox.setChecked(True)
        self.use_kill_list_checkbox = QCheckBox("Use Kill List")
        self.use_kill_list_checkbox.setChecked(True)
        self.terminate_bw_on_exit_checkbox = QCheckBox("Terminate Borderless on Exit")
        self.terminate_bw_on_exit_checkbox.setChecked(True)
        
        self.download_game_json_checkbox = QCheckBox("Download Game.json")
        self.download_game_json_checkbox.setToolTip("If checked, attempts to download game metadata from Steam using the Steam ID during creation.")

        # Index Sources moved to Database Indexing (General Options) section
        index_sources_button = QPushButton("INDEX SOURCES")
        index_sources_button.setStyleSheet("QPushButton { font-weight: bold; }")
        index_sources_button.clicked.connect(lambda: self.index_sources_requested.emit())

        # Create button shows dynamic count of selected items
        self.create_button = QPushButton()
        self.create_button.setStyleSheet("QPushButton { font-weight: bold; background-color: #4CAF50; color: white; padding: 8px; }")

        # Two-column layout for creation options: left = creation + enable items, right = runtime flags
        creation_columns_layout = QHBoxLayout()
        left_col = QVBoxLayout()
        right_col = QVBoxLayout()

        # Left column: Overwrite checkboxes for all 18 items
        overwrite_scroll = QScrollArea()
        overwrite_scroll.setWidgetResizable(True)
        overwrite_widget = QWidget()
        overwrite_layout = QVBoxLayout(overwrite_widget)
        overwrite_layout.setContentsMargins(0, 0, 0, 0)
        
        for key in PATH_KEYS:
            label = PATH_LABELS.get(key, f"Overwrite {key}")
            cb = QCheckBox(label)
            cb.setChecked(True)
            cb.stateChanged.connect(self.config_changed.emit)
            self.overwrite_checkboxes[key] = cb
            overwrite_layout.addWidget(cb)
            
        overwrite_scroll.setWidget(overwrite_widget)
        left_col.addWidget(overwrite_scroll)

        # Right column: runtime/creation flags requested to be on right
        right_col.addWidget(self.hide_taskbar_checkbox)
        right_col.addWidget(self.run_as_admin_checkbox)
        right_col.addWidget(self.use_kill_list_checkbox)
        right_col.addWidget(self.terminate_bw_on_exit_checkbox)
        right_col.addSpacing(20)
        right_col.addWidget(self.create_button)
        right_col.addWidget(self.download_game_json_checkbox, 0, Qt.AlignmentFlag.AlignRight)
        right_col.addStretch(1)

        creation_columns_layout.addLayout(left_col)
        creation_columns_layout.addLayout(right_col)
        creation_options_layout.addLayout(creation_columns_layout)

        # --- Accordion Setup ---
        # Rename General Options to Database Indexing
        general_options_section = AccordionSection("Database Indexing", general_options_widget)
        general_options_section.content_height += 75
        creation_section = AccordionSection("Creation", creation_options_widget)

        main_layout.addWidget(general_options_section)
        main_layout.addWidget(creation_section)
        main_layout.addStretch(1)

        # --- Connect Signals ---
        self.hide_taskbar_checkbox.stateChanged.connect(self.config_changed.emit)
        self.run_as_admin_checkbox.stateChanged.connect(self.config_changed.emit)
        self.name_check_checkbox.stateChanged.connect(self.config_changed.emit)
        self.steam_json_v1_radio.toggled.connect(self.config_changed.emit)
        self.steam_json_v2_radio.toggled.connect(self.config_changed.emit)
        self.use_kill_list_checkbox.stateChanged.connect(self.config_changed.emit)
        self.terminate_bw_on_exit_checkbox.stateChanged.connect(self.config_changed.emit)
        self.download_game_json_checkbox.stateChanged.connect(self.config_changed.emit)

        index_sources_button.clicked.connect(self.index_sources_requested.emit)
        self.create_button.clicked.connect(self.create_selected_requested.emit)
        self.download_steam_json_button.clicked.connect(self._on_download_clicked)
        self.delete_json_button.clicked.connect(self.delete_steam_json_requested.emit)
        self.delete_cache_button.clicked.connect(self.delete_steam_cache_requested.emit)
        self.process_json_button.clicked.connect(self.process_steam_json_requested.emit)

        # Add the Index Sources button into the general options area for prominence
        try:
            # place after the steam data buttons
            general_options_layout.addWidget(index_sources_button)
        except Exception:
            pass

        # Initialize and connect to editor tab data changes
        self.update_create_button_count()

    def update_create_button_count(self):
        """Update the create button text with the number of items marked for creation."""
        count = 0
        try:
            if hasattr(self.main_window, 'editor_tab'):
                count = self.main_window.editor_tab.get_create_count()
        except Exception:
            pass
        self.create_button.setText(f"CREATE {count} ITEMS")
        self.create_button.setEnabled(count > 0)

    def _on_download_clicked(self):
        """Emit the download signal with the currently selected version."""
        version = 1 if self.steam_json_v1_radio.isChecked() else 2
        self.download_steam_json_requested.emit(version)

    def highlight_unpopulated_items(self, main_window):
        """Highlight enable checkboxes in red if their corresponding setup items are not populated."""
        pass

    def sync_ui_from_config(self, config: AppConfig):
        """Updates the UI widgets with values from the AppConfig model."""
        self.blockSignals(True)

        self.hide_taskbar_checkbox.setChecked(config.hide_taskbar)
        self.run_as_admin_checkbox.setChecked(config.run_as_admin)
        self.name_check_checkbox.setChecked(config.enable_name_matching)
        
        if config.steam_json_version == 1:
            self.steam_json_v1_radio.setChecked(True)
        else:
            self.steam_json_v2_radio.setChecked(True)

        self.use_kill_list_checkbox.setChecked(config.use_kill_list)
        self.terminate_bw_on_exit_checkbox.setChecked(config.terminate_borderless_on_exit)
        self.download_game_json_checkbox.setChecked(config.download_game_json)
        
        # Sync overwrite checkboxes
        for key, cb in self.overwrite_checkboxes.items():
            cb.setChecked(config.overwrite_states.get(key, True))

        self.blockSignals(False)

    def sync_config_from_ui(self, config: AppConfig):
        """Updates the AppConfig model with values from the UI widgets."""
        config.hide_taskbar = self.hide_taskbar_checkbox.isChecked()
        config.run_as_admin = self.run_as_admin_checkbox.isChecked()
        config.enable_name_matching = self.name_check_checkbox.isChecked()
        config.steam_json_version = 1 if self.steam_json_v1_radio.isChecked() else 2

        config.use_kill_list = self.use_kill_list_checkbox.isChecked()
        config.terminate_borderless_on_exit = self.terminate_bw_on_exit_checkbox.isChecked()
        config.download_game_json = self.download_game_json_checkbox.isChecked()
        
        # Sync overwrite states
        for key, cb in self.overwrite_checkboxes.items():
            config.overwrite_states[key] = cb.isChecked()
