from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMenu, QWidget, QListWidget, QListWidgetItem, QCheckBox
)
from PyQt6.QtCore import Qt, QSize

def create_editor_tab_item_status_widget(parent, initial_text="", row=-1, col=-1, data_key=None):
    """Create a widget containing a checkbox for table cells
    
    Args:
        parent: The parent window/widget
        initial_text: Initial state as text ("true"/"false")
        row, col: Row and column for callback purposes
        data_key: Optional data key for callback data
        
    Returns:
        A widget containing a checkbox with proper state
    """
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
    
    # Create checkbox
    check = QCheckBox()
    check.setChecked(str(initial_text).lower() == "true")
    layout.addWidget(check, 0, Qt.AlignmentFlag.AlignCenter)
    
    # Connect to parent's edited handler if available
    if hasattr(parent, '_on_editor_table_edited'):
        check.stateChanged.connect(lambda state: parent._on_editor_table_edited(QTableWidgetItem()))
    
    return widget

def populate_editor_tab(main_window):
    """Populate the editor tab with all required UI elements"""
    # Check if the tab already has a layout
    if main_window.editor_tab.layout() is None:
        main_window.editor_tab_layout = QVBoxLayout(main_window.editor_tab)
    else:
        # Clear existing layout if it exists
        while main_window.editor_tab.layout().count():
            item = main_window.editor_tab.layout().takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        main_window.editor_tab_layout = main_window.editor_tab.layout()
    
    # Create button layout
    button_layout = QHBoxLayout()
    
    # Create index management button with dropdown menu
    main_window.index_button = QPushButton("Index")
    index_menu = QMenu(main_window.index_button)

    # Add actions to the menu
    load_action = index_menu.addAction("Load Index")
    load_action.triggered.connect(main_window._load_index)

    save_action = index_menu.addAction("Save Index")
    save_action.triggered.connect(main_window._save_editor_table_to_index)

    delete_action = index_menu.addAction("Delete Indexes")
    delete_action.triggered.connect(main_window._on_delete_indexes)

    main_window.index_button.setMenu(index_menu)
    button_layout.addWidget(main_window.index_button)
    
    # Add clear list view button
    main_window.clear_listview_button = QPushButton("Clear List-View")
    main_window.clear_listview_button.clicked.connect(main_window._on_clear_listview)
    button_layout.addWidget(main_window.clear_listview_button)
    
    # Add regenerate names button
    regenerate_names_button = QPushButton("Regenerate All Names")
    regenerate_names_button.clicked.connect(main_window._regenerate_all_names)
    regenerate_names_button.setToolTip("Regenerate all name overrides in the table")
    regenerate_names_button.setVisible(False)
    button_layout.addWidget(regenerate_names_button)
    
    # Add spacer to push buttons to the left
    button_layout.addStretch(1)
    
    # Note: CREATE button removed as it does nothing
    
    main_window.editor_tab_layout.addLayout(button_layout)
    
    # Create table for editing entries
    main_window.editor_table = QTableWidget()
    # Use central EditorCols mapping for column count
    from Python import constants
    main_window.editor_table.setColumnCount(max(c.value for c in constants.EditorCols) + 1)
    main_window.editor_table.setHorizontalHeaderLabels([
        "Create", "Name", "Directory", "SteamID",
        "NameOverride", "Options", "Arguments", "RunAsAdmin",
        "CM En", "Controller Mapper", "CM Rw",
        "BW En", "Borderless Windowing", "BW Rw",
        "MM En", "Multi-Monitor", "MM Rw",
        "Hide Taskbar",
        "MM Game Profile", "MM Desktop Profile", "Player 1 Profile", "Player 2 Profile", "MediaCenter Profile",
        "JA En", "Just After Launch", "JA Rw",
        "JB En", "Just Before Exit", "JB Rw",
        "Pre1En", "Pre1", "Pre1Rw", "Pst1En", "Post1", "Pst1Rw",
        "Pre2En", "Pre2", "Pre2Rw", "Pst2En", "Post2", "Pst2Rw",
        "Pre3En", "Pre3", "Pre3Rw", "Pst3En", "Post3", "Pst3Rw",
        "KL En", "Kill List"
    ])

    # Shorten width for Enabled (En) and Run/Wait (Rw) columns to save space
    try:
        en_columns = [constants.EditorCols.CM_ENABLED.value, constants.EditorCols.BW_ENABLED.value,
                      constants.EditorCols.MM_ENABLED.value, constants.EditorCols.JA_ENABLED.value,
                      constants.EditorCols.JB_ENABLED.value, constants.EditorCols.PRE1_ENABLED.value,
                      constants.EditorCols.POST1_ENABLED.value, constants.EditorCols.PRE2_ENABLED.value,
                      constants.EditorCols.POST2_ENABLED.value, constants.EditorCols.PRE3_ENABLED.value,
                      constants.EditorCols.POST3_ENABLED.value]
        
        # Hide the Enabled columns as they are now merged into the path columns
        for col in en_columns:
            main_window.editor_table.setColumnHidden(col, True)

        rw_columns = [constants.EditorCols.CM_RUN_WAIT.value, constants.EditorCols.BW_RUN_WAIT.value,
                      constants.EditorCols.MM_RUN_WAIT.value, constants.EditorCols.JA_RUN_WAIT.value,
                      constants.EditorCols.JB_RUN_WAIT.value, constants.EditorCols.PRE1_RUN_WAIT.value,
                      constants.EditorCols.POST1_RUN_WAIT.value, constants.EditorCols.PRE2_RUN_WAIT.value,
                      constants.EditorCols.POST2_RUN_WAIT.value, constants.EditorCols.PRE3_RUN_WAIT.value,
                      constants.EditorCols.POST3_RUN_WAIT.value]

        for col in rw_columns:
            # Use a conservative small width; UI can still resize if needed
            main_window.editor_table.setColumnWidth(col, 56)
    except Exception:
        # Fail silently if EditorCols are not available for any reason
        pass
    
    # Set column properties
    main_window.editor_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
    main_window.editor_table.horizontalHeader().setStretchLastSection(True)
    main_window.editor_table.verticalHeader().setVisible(False)
    
    # Connect signals
    main_window.editor_table.cellClicked.connect(main_window._on_editor_table_cell_left_click)
    main_window.editor_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    main_window.editor_table.customContextMenuRequested.connect(main_window._on_editor_table_custom_context_menu)
    main_window.editor_table.horizontalHeader().sectionClicked.connect(main_window._on_editor_table_header_click)
    
    main_window.editor_tab_layout.addWidget(main_window.editor_table)
    

    # Connect editor table signals
    main_window.editor_table.itemChanged.connect(main_window._on_editor_table_edited)

    # Also connect checkbox state changes
    def connect_checkbox_changes(table):
        """Connect checkbox state changes to the edited handler"""
        for row in range(table.rowCount()):
            for col in range(table.columnCount()):
                widget = table.cellWidget(row, col)
                if widget:
                    checkbox = widget.findChild(QCheckBox)
                    if checkbox:
                        # Get the main window reference
                        main_window = table.parent()
                        while main_window and not hasattr(main_window, '_on_editor_table_edited'):
                            main_window = main_window.parent()

                        if main_window and hasattr(main_window, '_on_editor_table_edited'):
                            checkbox.stateChanged.connect(
                                lambda state, mw=main_window: mw._on_editor_table_edited(None))

    # Call this function whenever rows are added to the table
    connect_checkbox_changes(main_window.editor_table)

    # Connect to rowsInserted signal to handle new rows
    main_window.editor_table.model().rowsInserted.connect(
        lambda parent, first, last, mw=main_window: connect_checkbox_changes(mw.editor_table))
