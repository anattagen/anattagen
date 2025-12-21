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
    process_steam_json_requested = pyqtSignal()
    
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

        row1_layout = QHBoxLayout()
        row1_layout.addWidget(self.net_check_checkbox)
        row1_layout.addStretch(1)
        general_options_layout.addLayout(row1_layout)

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
        
        self.create_profile_folders_checkbox = QCheckBox("Create Profile Folders")
        self.create_profile_folders_checkbox.setChecked(True)
        self.create_overwrite_launcher_checkbox = QCheckBox("Create/Overwrite Launcher")
        self.create_overwrite_launcher_checkbox.setChecked(True)
        self.create_overwrite_joystick_profiles_checkbox = QCheckBox("Create/Overwrite Joystick Profiles")
        self.create_overwrite_joystick_profiles_checkbox.setChecked(True)
        self.hide_taskbar_checkbox = QCheckBox("Hide Taskbar")
        self.hide_taskbar_checkbox.setChecked(False)
        self.run_as_admin_checkbox = QCheckBox("Run As Admin")
        self.run_as_admin_checkbox.setChecked(True)
        self.use_kill_list_checkbox = QCheckBox("Use Kill List")
        self.use_kill_list_checkbox.setChecked(True)
        self.enable_launcher_checkbox = QCheckBox("Enable Launcher")
        self.enable_launcher_checkbox.setChecked(True)
        self.apply_mapper_profiles_checkbox = QCheckBox("Apply Mapper Profiles")
        self.apply_mapper_profiles_checkbox.setChecked(True)
        self.enable_borderless_windowing_checkbox = QCheckBox("Enable Borderless Windowing")
        self.enable_borderless_windowing_checkbox.setChecked(True)
        self.terminate_bw_on_exit_checkbox = QCheckBox("Terminate Borderless on Exit")
        self.terminate_bw_on_exit_checkbox.setChecked(True)

        # Enable toggles for Applications (populated from Setup -> Applications)
        self.enable_controller_mapper_checkbox = QCheckBox("Enable Controller Mapper")
        self.enable_controller_mapper_checkbox.setChecked(True)
        self.enable_borderless_app_checkbox = QCheckBox("Enable Borderless App")
        self.enable_borderless_app_checkbox.setChecked(True)
        self.enable_multimonitor_app_checkbox = QCheckBox("Enable Multi-Monitor App")
        self.enable_multimonitor_app_checkbox.setChecked(True)
        self.enable_after_launch_app_checkbox = QCheckBox("Enable Just After Launch App")
        self.enable_after_launch_app_checkbox.setChecked(True)
        self.enable_before_exit_app_checkbox = QCheckBox("Enable Just Before Exit App")
        self.enable_before_exit_app_checkbox.setChecked(True)
        self.enable_pre1_checkbox = QCheckBox("Enable Pre-Launch App 1")
        self.enable_pre1_checkbox.setChecked(True)
        self.enable_pre2_checkbox = QCheckBox("Enable Pre-Launch App 2")
        self.enable_pre2_checkbox.setChecked(True)
        self.enable_pre3_checkbox = QCheckBox("Enable Pre-Launch App 3")
        self.enable_pre3_checkbox.setChecked(True)
        self.enable_post1_checkbox = QCheckBox("Enable Post-Launch App 1")
        self.enable_post1_checkbox.setChecked(True)
        self.enable_post2_checkbox = QCheckBox("Enable Post-Launch App 2")
        self.enable_post2_checkbox.setChecked(True)
        self.enable_post3_checkbox = QCheckBox("Enable Post-Launch App 3")
        self.enable_post3_checkbox.setChecked(True)

        # Index Sources moved to Database Indexing (General Options) section
        index_sources_button = QPushButton("INDEX SOURCES")
        index_sources_button.setStyleSheet("QPushButton { font-weight: bold; }")
        index_sources_button.clicked.connect(lambda: self.index_sources_requested.emit())

        # Create button shows dynamic count of selected items
        create_button = QPushButton()
        create_button.setStyleSheet("QPushButton { font-weight: bold; background-color: #4CAF50; color: white; padding: 8px; }")

        # Two-column layout for creation options: left = creation + enable items, right = runtime flags
        creation_columns_layout = QHBoxLayout()
        left_col = QVBoxLayout()
        right_col = QVBoxLayout()

        # Left column: creation options + enable toggles for apps
        left_col.addWidget(self.create_profile_folders_checkbox)
        left_col.addWidget(self.create_overwrite_launcher_checkbox)
        left_col.addWidget(self.create_overwrite_joystick_profiles_checkbox)
        left_col.addSpacing(6)
        left_col.addWidget(self.enable_controller_mapper_checkbox)
        left_col.addWidget(self.enable_borderless_app_checkbox)
        left_col.addWidget(self.enable_multimonitor_app_checkbox)
        left_col.addWidget(self.enable_after_launch_app_checkbox)
        left_col.addWidget(self.enable_before_exit_app_checkbox)
        left_col.addWidget(self.enable_pre1_checkbox)
        left_col.addWidget(self.enable_pre2_checkbox)
        left_col.addWidget(self.enable_pre3_checkbox)
        left_col.addWidget(self.enable_post1_checkbox)
        left_col.addWidget(self.enable_post2_checkbox)
        left_col.addWidget(self.enable_post3_checkbox)
        left_col.addStretch(1)

        # Right column: runtime/creation flags requested to be on right
        right_col.addWidget(self.hide_taskbar_checkbox)
        right_col.addWidget(self.run_as_admin_checkbox)
        right_col.addWidget(self.use_kill_list_checkbox)
        right_col.addWidget(self.terminate_bw_on_exit_checkbox)
        right_col.addWidget(self.enable_launcher_checkbox)
        right_col.addWidget(self.apply_mapper_profiles_checkbox)
        right_col.addWidget(self.enable_borderless_windowing_checkbox)
        right_col.addSpacing(6)
        right_col.addWidget(create_button)
        right_col.addStretch(1)

        creation_columns_layout.addLayout(left_col)
        creation_columns_layout.addLayout(right_col)
        creation_options_layout.addLayout(creation_columns_layout)

        # --- Accordion Setup ---
        # Rename General Options to Database Indexing
        general_options_section = AccordionSection("Database Indexing", general_options_widget)
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
        self.use_kill_list_checkbox.stateChanged.connect(self.config_changed.emit)
        self.enable_launcher_checkbox.stateChanged.connect(self.config_changed.emit)
        self.apply_mapper_profiles_checkbox.stateChanged.connect(self.config_changed.emit)
        self.enable_borderless_windowing_checkbox.stateChanged.connect(self.config_changed.emit)
        self.terminate_bw_on_exit_checkbox.stateChanged.connect(self.config_changed.emit)

        index_sources_button.clicked.connect(self.index_sources_requested.emit)
        create_button.clicked.connect(self.create_selected_requested.emit)
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

        # Configure dynamic create button text based on checked items in editor table
        def _update_create_button_text():
            try:
                wnd = self.window()
                if hasattr(wnd, 'editor_tab') and hasattr(wnd.editor_tab, 'table'):
                    table = wnd.editor_tab.table
                    count = 0
                    # Count checked checkboxes in column 0 (Create column)
                    for row in range(table.rowCount()):
                        cell_widget = table.cellWidget(row, 0)  # Column 0 is "Create"
                        if cell_widget is not None:
                            # Look for QCheckBox in the cell widget
                            from PyQt6.QtWidgets import QCheckBox
                            checkbox = None
                            if isinstance(cell_widget, QCheckBox):
                                checkbox = cell_widget
                            else:
                                # Search for checkbox in child widgets
                                for child in cell_widget.findChildren(QCheckBox):
                                    checkbox = child
                                    break
                            if checkbox and checkbox.isChecked():
                                count += 1
                else:
                    count = 0
            except Exception:
                count = 0
            try:
                create_button.setText(f"CREATE  [{count}]  ITEMS")
            except Exception:
                create_button.setText(f"CREATE  [0]  ITEMS")

        # Initialize and connect checkbox change signals if possible
        try:
            _update_create_button_text()
            wnd = self.window()
            if hasattr(wnd, 'editor_tab') and hasattr(wnd.editor_tab, 'table'):
                # Connect to itemChanged which fires when cells are modified (including checkboxes)
                wnd.editor_tab.table.itemChanged.connect(_update_create_button_text)
        except Exception:
            pass

        # Wire create button click to signal
        create_button.clicked.connect(self.create_selected_requested.emit)

    def _on_download_clicked(self):
        """Emit the download signal with the currently selected version."""
        version = 1 if self.steam_json_v1_radio.isChecked() else 2
        self.download_steam_json_requested.emit(version)

    def highlight_unpopulated_items(self, main_window):
        """Highlight enable checkboxes in red if their corresponding setup items are not populated."""
        # Map each enable checkbox to its corresponding setup item path
        items_to_check = {
            self.enable_controller_mapper_checkbox: getattr(main_window, 'controller_mapper_app_line_edit', None),
            self.enable_borderless_app_checkbox: getattr(main_window, 'borderless_app_line_edit', None),
            self.enable_multimonitor_app_checkbox: getattr(main_window, 'multimonitor_app_line_edit', None),
            self.enable_after_launch_app_checkbox: getattr(main_window, 'after_launch_app_line_edit', None),
            self.enable_before_exit_app_checkbox: getattr(main_window, 'before_exit_app_line_edit', None),
            self.enable_pre1_checkbox: getattr(main_window, 'pre_launch_app_line_edits', [None])[0] if hasattr(main_window, 'pre_launch_app_line_edits') and len(main_window.pre_launch_app_line_edits) > 0 else None,
            self.enable_pre2_checkbox: getattr(main_window, 'pre_launch_app_line_edits', [None, None])[1] if hasattr(main_window, 'pre_launch_app_line_edits') and len(main_window.pre_launch_app_line_edits) > 1 else None,
            self.enable_pre3_checkbox: getattr(main_window, 'pre_launch_app_line_edits', [None, None, None])[2] if hasattr(main_window, 'pre_launch_app_line_edits') and len(main_window.pre_launch_app_line_edits) > 2 else None,
            self.enable_post1_checkbox: getattr(main_window, 'post_launch_app_line_edits', [None])[0] if hasattr(main_window, 'post_launch_app_line_edits') and len(main_window.post_launch_app_line_edits) > 0 else None,
            self.enable_post2_checkbox: getattr(main_window, 'post_launch_app_line_edits', [None, None])[1] if hasattr(main_window, 'post_launch_app_line_edits') and len(main_window.post_launch_app_line_edits) > 1 else None,
            self.enable_post3_checkbox: getattr(main_window, 'post_launch_app_line_edits', [None, None, None])[2] if hasattr(main_window, 'post_launch_app_line_edits') and len(main_window.post_launch_app_line_edits) > 2 else None,
        }
        
        # Light red color for unpopulated items
        red_style = "color: #ff9999;"
        normal_style = ""
        
        for checkbox, line_edit in items_to_check.items():
            if line_edit and hasattr(line_edit, 'text'):
                # Check if the field is empty
                if not line_edit.text().strip():
                    # Apply red styling to checkbox text
                    checkbox.setStyleSheet(red_style)
                else:
                    checkbox.setStyleSheet(normal_style)
            else:
                checkbox.setStyleSheet(normal_style)

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
        self.use_kill_list_checkbox.setChecked(config.use_kill_list)
        self.enable_launcher_checkbox.setChecked(config.enable_launcher)
        self.apply_mapper_profiles_checkbox.setChecked(config.apply_mapper_profiles)
        self.enable_borderless_windowing_checkbox.setChecked(config.enable_borderless_windowing)
        self.terminate_bw_on_exit_checkbox.setChecked(config.terminate_borderless_on_exit)
        
        # Populate enable toggles for applications
        try:
            self.enable_controller_mapper_checkbox.setChecked(config.enable_controller_mapper)
            self.enable_borderless_app_checkbox.setChecked(config.enable_borderless_app)
            self.enable_multimonitor_app_checkbox.setChecked(config.enable_multimonitor_app)
            self.enable_after_launch_app_checkbox.setChecked(config.enable_after_launch_app)
            self.enable_before_exit_app_checkbox.setChecked(config.enable_before_exit_app)
            self.enable_pre1_checkbox.setChecked(config.enable_pre1)
            self.enable_pre2_checkbox.setChecked(config.enable_pre2)
            self.enable_pre3_checkbox.setChecked(config.enable_pre3)
            self.enable_post1_checkbox.setChecked(config.enable_post1)
            self.enable_post2_checkbox.setChecked(config.enable_post2)
            self.enable_post3_checkbox.setChecked(config.enable_post3)
        except Exception:
            pass

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
        config.use_kill_list = self.use_kill_list_checkbox.isChecked()
        config.enable_launcher = self.enable_launcher_checkbox.isChecked()
        config.apply_mapper_profiles = self.apply_mapper_profiles_checkbox.isChecked()
        config.enable_borderless_windowing = self.enable_borderless_windowing_checkbox.isChecked()
        config.terminate_borderless_on_exit = self.terminate_bw_on_exit_checkbox.isChecked()
        
        # Save enable toggles for applications
        try:
            config.enable_controller_mapper = self.enable_controller_mapper_checkbox.isChecked()
            config.enable_borderless_app = self.enable_borderless_app_checkbox.isChecked()
            config.enable_multimonitor_app = self.enable_multimonitor_app_checkbox.isChecked()
            config.enable_after_launch_app = self.enable_after_launch_app_checkbox.isChecked()
            config.enable_before_exit_app = self.enable_before_exit_app_checkbox.isChecked()
            config.enable_pre1 = self.enable_pre1_checkbox.isChecked()
            config.enable_pre2 = self.enable_pre2_checkbox.isChecked()
            config.enable_pre3 = self.enable_pre3_checkbox.isChecked()
            config.enable_post1 = self.enable_post1_checkbox.isChecked()
            config.enable_post2 = self.enable_post2_checkbox.isChecked()
            config.enable_post3 = self.enable_post3_checkbox.isChecked()
        except Exception:
            pass
