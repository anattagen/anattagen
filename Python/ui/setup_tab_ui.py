import os 
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QPushButton,
    QLineEdit, QHBoxLayout, QFormLayout, QFileDialog, QCheckBox, QAbstractItemView, QSpinBox, QRadioButton, QButtonGroup
)
from PyQt6.QtGui import QFontDatabase
from .ui_widgets import (
    create_path_selection_widget,
    create_app_selection_with_flyout_widget,
    create_app_selection_with_run_wait_widget,
    create_list_management_widget
)
from .config_manager import show_import_configuration_dialog
from .accordion import AccordionSection

def create_path_with_cen_lc_widget(main_window, dialog_title, is_directory=False):
    """Create a path selection widget with CEN/LC radio buttons."""
    widget = QWidget()
    layout = QHBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)
    
    # Line edit for path
    line_edit = QLineEdit()
    layout.addWidget(line_edit)
    
    # Browse button
    browse_btn = QPushButton(". . .")
    browse_btn.setFixedWidth(40)
    def open_dialog():
        if is_directory:
            path = QFileDialog.getExistingDirectory(main_window, dialog_title)
        else:
            path, _ = QFileDialog.getOpenFileName(main_window, dialog_title)
        if path:
            line_edit.setText(path)
    browse_btn.clicked.connect(open_dialog)
    layout.addWidget(browse_btn)
    
    # CEN/LC radio buttons
    cen_radio = QRadioButton("CEN")
    lc_radio = QRadioButton("LC")
    cen_radio.setChecked(True)
    mode_group = QButtonGroup(widget)
    mode_group.addButton(cen_radio)
    mode_group.addButton(lc_radio)
    layout.addWidget(cen_radio)
    layout.addWidget(lc_radio)
    
    # Store radio buttons on the widget for later access
    widget.line_edit = line_edit
    widget.cen_radio = cen_radio
    widget.lc_radio = lc_radio
    widget.mode_group = mode_group
    
    return widget, line_edit, cen_radio, lc_radio

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
    
    # Source (using QListWidget with drag-drop for consistency with SetupTab)
    from PyQt6.QtWidgets import QListWidget
    main_window.source_dirs_list = QListWidget()
    main_window.source_dirs_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
    main_window.source_dirs_list.setMaximumHeight(80)
    source_dirs_layout = QHBoxLayout()
    source_dirs_layout.addWidget(QLabel("Sources:"))
    source_dirs_layout.addWidget(main_window.source_dirs_list, 1)
    source_dirs_add_button = QPushButton("Add...")
    source_dirs_add_button.clicked.connect(lambda: main_window._add_to_list(main_window.source_dirs_list, "Select Source Directory", is_directory=True))
    source_dirs_remove_button = QPushButton("Remove")
    source_dirs_remove_button.clicked.connect(lambda: main_window._remove_from_list(main_window.source_dirs_list))
    source_dirs_layout.addWidget(source_dirs_add_button)
    source_dirs_layout.addWidget(source_dirs_remove_button)
    source_config_layout.addLayout(source_dirs_layout)
    main_window.source_dirs_list.setObjectName("source_dirs_list")
    
    # Excluded Items (using QListWidget with drag-drop)
    main_window.excluded_dirs_list = QListWidget()
    main_window.excluded_dirs_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
    main_window.excluded_dirs_list.setMaximumHeight(80)
    excluded_layout = QHBoxLayout()
    excluded_label = QLabel("Excluded Items:")
    excluded_layout.addWidget(excluded_label)
    excluded_layout.addWidget(main_window.excluded_dirs_list, 1)
    excluded_add_button = QPushButton("+")
    excluded_add_button.setFixedWidth(30)
    excluded_remove_button = QPushButton("x")
    excluded_remove_button.setFixedWidth(30)
    excluded_add_button.clicked.connect(lambda: main_window._add_to_list(main_window.excluded_dirs_list, "Enter Item to Exclude"))
    excluded_remove_button.clicked.connect(lambda: main_window._remove_from_list(main_window.excluded_dirs_list))
    excluded_layout.addWidget(excluded_add_button)
    excluded_layout.addWidget(excluded_remove_button)
    source_config_layout.addLayout(excluded_layout)
    main_window.excluded_dirs_list.setObjectName("excluded_dirs_list")
    
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
    
    # Font Dropdown
    main_window.font_combo = QComboBox()
    main_window.font_combo.addItem("System")
    site_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "site")
    if not os.path.exists(site_path):
        site_path = os.path.join(os.path.dirname(__file__), "site")
    if os.path.exists(site_path):
        for f in os.listdir(site_path):
            if f.lower().endswith((".ttf", ".otf")):
                main_window.font_combo.addItem(f)
    logging_layout.addWidget(QLabel("Font:"))
    logging_layout.addWidget(main_window.font_combo)

    # Font Size SpinBox
    main_window.font_size_spin = QSpinBox()
    main_window.font_size_spin.setRange(8, 24)
    main_window.font_size_spin.setValue(10)
    main_window.font_size_spin.valueChanged.connect(main_window._on_appearance_changed)
    logging_layout.addWidget(QLabel("Size:"))
    logging_layout.addWidget(main_window.font_size_spin)

    # Theme Dropdown
    main_window.theme_combo = QComboBox()
    main_window.theme_combo.addItems(["Default", "Windows", "Vista", "MacOS", "Fusion", "Dark", "Light"])
    main_window.theme_combo.currentTextChanged.connect(main_window._on_appearance_changed)
    logging_layout.addWidget(QLabel("Theme:"))
    logging_layout.addWidget(main_window.theme_combo)

    # Restart Button
    main_window.restart_btn = QPushButton("*")
    main_window.restart_btn.setToolTip("Reset application configuration to defaults")
    main_window.restart_btn.setFixedWidth(25)
    main_window.restart_btn.clicked.connect(main_window._reset_to_defaults)
    logging_layout.addWidget(main_window.restart_btn)
    
    # Set object names for persistence
    main_window.logging_verbosity_combo.setObjectName("logging_verbosity_combo")
    main_window.font_combo.setObjectName("font_combo")
    main_window.font_size_spin.setObjectName("font_size_spin")
    main_window.theme_combo.setObjectName("theme_combo")
    main_window.restart_btn.setObjectName("restart_btn")
    
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
    
    # Add path selection widgets
    widget, main_window.profiles_dir_edit = create_path_selection_widget(main_window, "Select Profiles Directory", is_directory=True)
    directories_layout.addRow(QLabel("Profiles:"), widget)
    widget, main_window.launchers_dir_edit = create_path_selection_widget(main_window, "Select Launchers Directory", is_directory=True)
    directories_layout.addRow(QLabel("Launchers:"), widget)
    
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
    
    # Add Just After Launch App
    widget, main_window.after_launch_app_line_edit, main_window.after_launch_run_wait_checkbox = create_app_selection_with_run_wait_widget(
        main_window, "Select Just After Launch App", main_window.predefined_controller_apps
    )
    applications_layout.addRow(QLabel("Just After Launch App:"), widget)

    # Add Just Before Exit App
    widget, main_window.before_exit_app_line_edit, main_window.before_exit_run_wait_checkbox = create_app_selection_with_run_wait_widget(
        main_window, "Select Just Before Exit App", main_window.predefined_controller_apps
    )
    applications_layout.addRow(QLabel("Just Before Exit App:"), widget)

    # Create pre-launch and post-launch app lists (placed in Applications section)
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
        applications_layout.addRow(QLabel(f"Pre-Launch App {i}:"), widget)
    
    for i in range(1, 4):
        widget, line_edit, run_wait_cb = create_app_selection_with_run_wait_widget(
            main_window, f"Select Post-Launch App {i}", predefined_run_wait_apps_template
        )
        main_window.post_launch_app_line_edits.append(line_edit)
        main_window.post_launch_run_wait_checkboxes.append(run_wait_cb)
        applications_layout.addRow(QLabel(f"Post-Launch App {i}:"), widget)

    # --- Section 3: Profiles ---
    profiles_widget = QWidget()
    profiles_layout = QFormLayout(profiles_widget)
    
    # Add profile selection widgets with CEN/LC
    p1_widget, main_window.p1_profile_edit, main_window.p1_cen_radio, main_window.p1_lc_radio = create_path_with_cen_lc_widget(main_window, "Select Player 1 Profile File", is_directory=False)
    profiles_layout.addRow(QLabel("Player 1 Profile File:"), p1_widget)
    p2_widget, main_window.p2_profile_edit, main_window.p2_cen_radio, main_window.p2_lc_radio = create_path_with_cen_lc_widget(main_window, "Select Player 2 Profile File", is_directory=False)
    profiles_layout.addRow(QLabel("Player 2 Profile File:"), p2_widget)
    mediacenter_widget, main_window.mediacenter_profile_edit, main_window.mediacenter_cen_radio, main_window.mediacenter_lc_radio = create_path_with_cen_lc_widget(main_window, "Select Media Center/Desktop Profile File", is_directory=False)
    profiles_layout.addRow(QLabel("Media Center/Desktop Profile File:"), mediacenter_widget)
    
    multimonitor_gaming_widget, main_window.multimonitor_gaming_config_edit, main_window.multimonitor_gaming_cen_radio, main_window.multimonitor_gaming_lc_radio = create_path_with_cen_lc_widget(main_window, "Select Multi-Monitor Gaming Config File", is_directory=False)
    profiles_layout.addRow(QLabel("Multi-Monitor Gaming Config File:"), multimonitor_gaming_widget)
    multimonitor_media_widget, main_window.multimonitor_media_config_edit, main_window.multimonitor_media_cen_radio, main_window.multimonitor_media_lc_radio = create_path_with_cen_lc_widget(main_window, "Select Multi-Monitor Media/Desktop Config File", is_directory=False)
    profiles_layout.addRow(QLabel("Multi-Monitor Media/Desktop Config File:"), multimonitor_media_widget)
    
    # (Pre/Post launch app widgets moved into Applications section)
    
    # Create accordion sections
    source_config_section = AccordionSection("Source Configuration", source_config_widget)
    directories_section = AccordionSection("Paths", directories_widget)
    applications_section = AccordionSection("Applications", applications_widget)
    profiles_section = AccordionSection("Profiles", profiles_widget)
    
    # Add sections to main layout
    main_layout.addWidget(source_config_section)
    main_layout.addWidget(directories_section)
    main_layout.addWidget(applications_section)
    main_layout.addWidget(profiles_section)
    main_layout.addStretch(1)
    
    # Set object names for config saving/loading
    main_window.source_dirs_list.setObjectName("source_dirs_list")
    main_window.excluded_dirs_list.setObjectName("excluded_dirs_list")
    main_window.logging_verbosity_combo.setObjectName("logging_verbosity_combo")
    main_window.font_combo.setObjectName("font_combo")
    main_window.font_size_spin.setObjectName("font_size_spin")
    main_window.theme_combo.setObjectName("theme_combo")
    main_window.restart_btn.setObjectName("restart_btn")
    main_window.profiles_dir_edit.setObjectName("profiles_dir_edit")
    main_window.launchers_dir_edit.setObjectName("launchers_dir_edit")
    main_window.controller_mapper_app_line_edit.setObjectName("controller_mapper_app_line_edit")
    main_window.borderless_app_line_edit.setObjectName("borderless_app_line_edit")
    main_window.multimonitor_app_line_edit.setObjectName("multimonitor_app_line_edit")
    main_window.after_launch_app_line_edit.setObjectName("after_launch_app_line_edit")
    main_window.before_exit_app_line_edit.setObjectName("before_exit_app_line_edit")
    main_window.after_launch_run_wait_checkbox.setObjectName("after_launch_run_wait_checkbox")
    main_window.before_exit_run_wait_checkbox.setObjectName("before_exit_run_wait_checkbox")
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
