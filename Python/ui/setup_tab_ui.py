import os 
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QPushButton,
    QLineEdit, QHBoxLayout, QFormLayout, QFileDialog, QCheckBox
)
from .ui_widgets import (
    create_path_selection_widget,
    create_app_selection_with_flyout_widget,
    create_app_selection_with_run_wait_widget,
    create_list_management_widget
)
from .config_manager import show_import_configuration_dialog
from .accordion import AccordionSection

def populate_setup_tab(main_window: QWidget):
    """Populate the setup tab with UI elements"""
    from PyQt6.QtWidgets import (
        QLabel, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, 
        QPushButton, QFileDialog, QWidget, QGroupBox, QComboBox
    )
    from PyQt6.QtCore import Qt
    from .ui_widgets import create_path_selection_widget, create_app_selection_with_flyout_widget, create_app_selection_with_run_wait_widget, create_list_management_widget
    from .accordion import AccordionSection
    
    # Check if the tab already has a layout
    if main_window.setup_tab.layout() is None:
        main_window.setup_tab_layout = QVBoxLayout(main_window.setup_tab)
    else:
        # Clear existing layout if it exists
        while main_window.setup_tab.layout().count():
            item = main_window.setup_tab.layout().takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        main_window.setup_tab_layout = main_window.setup_tab.layout()
    
    # Create a main layout for the setup tab
    main_layout = QVBoxLayout()
    main_layout.setContentsMargins(10, 10, 10, 10)
    
    # --- Section 0: Source Configuration ---
    source_config_widget = QWidget()
    source_config_layout = QVBoxLayout(source_config_widget)
    
    # Source directories
    source_dirs_layout = QHBoxLayout()
    source_dirs_layout.addWidget(QLabel("Source Directories:"))
    main_window.source_dirs_combo = QComboBox()
    main_window.source_dirs_combo.setEditable(True)
    main_window.source_dirs_combo.setMinimumWidth(300)
    source_dirs_layout.addWidget(main_window.source_dirs_combo)
    
    # Add buttons for source directory management
    source_dirs_add_button = QPushButton("Add")
    source_dirs_add_button.clicked.connect(lambda: main_window._add_to_combo(main_window.source_dirs_combo, "Select Source Directory", is_directory=True))
    source_dirs_layout.addWidget(source_dirs_add_button)
    
    source_dirs_remove_button = QPushButton("Remove")
    source_dirs_remove_button.clicked.connect(lambda: main_window._remove_from_combo(main_window.source_dirs_combo))
    source_dirs_layout.addWidget(source_dirs_remove_button)
    
    source_config_layout.addLayout(source_dirs_layout)
    
    # Exclude items
    exclude_items_layout = QHBoxLayout()
    exclude_items_layout.addWidget(QLabel("Exclude Items:"))
    main_window.exclude_items_combo = QComboBox()
    main_window.exclude_items_combo.setEditable(True)
    main_window.exclude_items_combo.setMinimumWidth(300)
    exclude_items_layout.addWidget(main_window.exclude_items_combo)
    
    # Add buttons for exclude items management
    exclude_items_add_button = QPushButton("Add")
    exclude_items_add_button.clicked.connect(lambda: main_window._add_to_combo(main_window.exclude_items_combo, "Enter Item to Exclude"))
    exclude_items_layout.addWidget(exclude_items_add_button)
    
    exclude_items_remove_button = QPushButton("Remove")
    exclude_items_remove_button.clicked.connect(lambda: main_window._remove_from_combo(main_window.exclude_items_combo))
    exclude_items_layout.addWidget(exclude_items_remove_button)
    
    source_config_layout.addLayout(exclude_items_layout)
    
    # Game managers
    game_managers_layout = QHBoxLayout()
    game_managers_layout.addWidget(QLabel("Game Managers Present:"))
    main_window.other_managers_combo = QComboBox()
    main_window.other_managers_combo.addItems(["None", "Steam", "Epic", "GOG", "Origin", "Ubisoft Connect", "Battle.net", "Xbox"])
    game_managers_layout.addWidget(main_window.other_managers_combo)
    
    main_window.exclude_manager_checkbox = QCheckBox("Exclude Selected Manager's Games")
    game_managers_layout.addWidget(main_window.exclude_manager_checkbox)
    game_managers_layout.addStretch(1)
    
    source_config_layout.addLayout(game_managers_layout)
    
    # Logging verbosity
    logging_layout = QHBoxLayout()
    logging_layout.addWidget(QLabel("Logging Verbosity:"))
    main_window.logging_verbosity_combo = QComboBox()
    main_window.logging_verbosity_combo.addItems(["None", "Low", "Medium", "High", "Debug"])
    main_window.logging_verbosity_combo.currentTextChanged.connect(main_window._on_logging_verbosity_changed)
    logging_layout.addWidget(main_window.logging_verbosity_combo)
    logging_layout.addStretch(1)
    
    source_config_layout.addLayout(logging_layout)
    
    # --- Section 1: Directories ---
    directories_widget = QWidget()
    directories_layout = QFormLayout(directories_widget)
    
    # Create predefined app dictionaries
    main_window.predefined_controller_apps = {
        "AntimicroX": "Path/To/AntimicroX.exe", "Keysticks": "Path/To/Keysticks.exe",
        "DS4Windows": "Path/To/DS4Windows.exe", "JoyXoff": "Path/To/JoyXoff.exe",
        "SteamInput": "Configure within Steam", 
        "Add New...": main_window._add_new_app_dialog
    }
    main_window.predefined_borderless_apps = {
        "Magpie": "Path/To/Magpie.exe", "Borderless Gaming": "Path/To/BorderlessGaming.exe",
        "Special K": "Path/To/SpecialK.exe",
        "Add New...": main_window._add_new_app_dialog
    }
    main_window.predefined_multimonitor_apps = {
        "MultiMonitorTool": "Path/To/MultiMonitorTool.exe", "Display-Changer": "Path/To/Display-Changer.exe",
        "Script": "Path/To/YourMultiMonitorScript.bat", 
        "Add New...": main_window._add_new_app_dialog
    }
    
    # Add directory selection widgets
    widget, main_window.profiles_dir_edit = create_path_selection_widget(main_window, "Select Profiles Directory", is_directory=True)
    directories_layout.addRow(QLabel("Profiles Directory:"), widget)
    widget, main_window.launchers_dir_edit = create_path_selection_widget(main_window, "Select Launchers Directory", is_directory=True)
    directories_layout.addRow(QLabel("Launchers Directory:"), widget)
    
    # --- Section 2: Applications ---
    applications_widget = QWidget()
    applications_layout = QFormLayout(applications_widget)
    
    # Add application selection widgets
    widget, main_window.controller_mapper_app_line_edit = create_app_selection_with_flyout_widget(
        main_window, "Select Controller Mapper Application", main_window.predefined_controller_apps
    )
    applications_layout.addRow(QLabel("Controller Mapper Application:"), widget)
    
    widget, main_window.borderless_app_line_edit = create_app_selection_with_flyout_widget(
        main_window, "Select Borderless Window Application", main_window.predefined_borderless_apps
    )
    applications_layout.addRow(QLabel("Borderless Window Application:"), widget)
    
    widget, main_window.multimonitor_app_line_edit = create_app_selection_with_flyout_widget(
        main_window, "Select Multi-Monitor Application", main_window.predefined_multimonitor_apps
    )
    applications_layout.addRow(QLabel("Multi-Monitor Application:"), widget)
    
    # --- Section 3: Profiles ---
    profiles_widget = QWidget()
    profiles_layout = QFormLayout(profiles_widget)
    
    # Add profile selection widgets
    widget, main_window.p1_profile_edit = create_path_selection_widget(main_window, "Select Player 1 Profile File", is_directory=False)
    profiles_layout.addRow(QLabel("Player 1 Profile File:"), widget)
    widget, main_window.p2_profile_edit = create_path_selection_widget(main_window, "Select Player 2 Profile File", is_directory=False)
    profiles_layout.addRow(QLabel("Player 2 Profile File:"), widget)
    widget, main_window.mediacenter_profile_edit = create_path_selection_widget(main_window, "Select Media Center/Desktop Profile File", is_directory=False)
    profiles_layout.addRow(QLabel("Media Center/Desktop Profile File:"), widget)
    
    widget, main_window.multimonitor_gaming_config_edit = create_path_selection_widget(main_window, "Select Multi-Monitor Gaming Config File", is_directory=False)
    profiles_layout.addRow(QLabel("Multi-Monitor Gaming Config File:"), widget)
    widget, main_window.multimonitor_media_config_edit = create_path_selection_widget(main_window, "Select Multi-Monitor Media/Desktop Config File", is_directory=False)
    profiles_layout.addRow(QLabel("Multi-Monitor Media/Desktop Config File:"), widget)
    
    # Create pre-launch and post-launch app lists
    main_window.pre_launch_app_line_edits = []
    main_window.pre_launch_run_wait_checkboxes = []
    main_window.post_launch_app_line_edits = []
    main_window.post_launch_run_wait_checkboxes = []
    
    # For apps with Run-Wait
    predefined_run_wait_apps_template = {
        "Add New...": main_window._add_new_app_dialog
    }
    
    for i in range(1, 4):
        widget, line_edit, run_wait_cb = create_app_selection_with_run_wait_widget(
            main_window, f"Select Pre-Launch App {i}", predefined_run_wait_apps_template
        )
        main_window.pre_launch_app_line_edits.append(line_edit)
        main_window.pre_launch_run_wait_checkboxes.append(run_wait_cb)
        profiles_layout.addRow(QLabel(f"Pre-Launch App {i}:"), widget)
    
    for i in range(1, 4):
        widget, line_edit, run_wait_cb = create_app_selection_with_run_wait_widget(
            main_window, f"Select Post-Launch App {i}", predefined_run_wait_apps_template
        )
        main_window.post_launch_app_line_edits.append(line_edit)
        main_window.post_launch_run_wait_checkboxes.append(run_wait_cb)
        profiles_layout.addRow(QLabel(f"Post-Launch App {i}:"), widget)
    
    # Create accordion sections
    source_config_section = AccordionSection("Source Configuration", source_config_widget)
    directories_section = AccordionSection("Directories", directories_widget)
    applications_section = AccordionSection("Applications", applications_widget)
    profiles_section = AccordionSection("Profiles", profiles_widget)
    
    # Add sections to main layout
    main_layout.addWidget(source_config_section)
    main_layout.addWidget(directories_section)
    main_layout.addWidget(applications_section)
    main_layout.addWidget(profiles_section)
    main_layout.addStretch(1)
    
    # Set object names for config saving/loading
    main_window.source_dirs_combo.setObjectName("source_dirs_combo")
    main_window.exclude_items_combo.setObjectName("exclude_items_combo")
    main_window.other_managers_combo.setObjectName("other_managers_combo")
    main_window.logging_verbosity_combo.setObjectName("logging_verbosity_combo")
    main_window.exclude_manager_checkbox.setObjectName("exclude_manager_checkbox")
    main_window.profiles_dir_edit.setObjectName("profiles_dir_edit")
    main_window.launchers_dir_edit.setObjectName("launchers_dir_edit")
    main_window.controller_mapper_app_line_edit.setObjectName("controller_mapper_app_line_edit")
    main_window.borderless_app_line_edit.setObjectName("borderless_app_line_edit")
    main_window.multimonitor_app_line_edit.setObjectName("multimonitor_app_line_edit")
    main_window.p1_profile_edit.setObjectName("p1_profile_edit")
    main_window.p2_profile_edit.setObjectName("p2_profile_edit")
    main_window.mediacenter_profile_edit.setObjectName("mediacenter_profile_edit")
    main_window.multimonitor_gaming_config_edit.setObjectName("multimonitor_gaming_config_edit")
    main_window.multimonitor_media_config_edit.setObjectName("multimonitor_media_config_edit")
    
    # Set object names for pre-launch and post-launch app line edits
    for i, line_edit in enumerate(main_window.pre_launch_app_line_edits):
        line_edit.setObjectName(f"pre_launch_app_line_edit_{i}")
    for i, line_edit in enumerate(main_window.post_launch_app_line_edits):
        line_edit.setObjectName(f"post_launch_app_line_edit_{i}")
    
    # Add the main layout to the setup tab
    main_window.setup_tab_layout.addLayout(main_layout)
    
    # Print debug info
    print("Setup tab populated successfully")
