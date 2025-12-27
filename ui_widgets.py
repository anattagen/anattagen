from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QPushButton, QFileDialog,
    QToolButton, QMenu, QCheckBox, QComboBox, QButtonGroup, QRadioButton
)
from PyQt6.QtCore import Qt # Might be needed for alignments or flags

# Note: Lambdas used for QFileDialog connections might need careful handling
# if they capture loop variables or rely on specific 'self' context from MainWindow.
# For now, 'parent_window' will be used as the parent for dialogs.

def create_file_browser_widget(parent_window, dialog_title_text, is_directory=True, line_edit_instance=None):
    widget = QWidget()
    layout = QHBoxLayout(widget)
    layout.setContentsMargins(0,0,0,0)
    line_edit = line_edit_instance if line_edit_instance else QLineEdit()
    layout.addWidget(line_edit, 1)
    button = QPushButton("Browse")
    def open_dialog():
        if is_directory:
            path = QFileDialog.getExistingDirectory(parent_window, dialog_title_text)
        else:
            path, _ = QFileDialog.getOpenFileName(parent_window, dialog_title_text)
        if path:
            line_edit.setText(path)
    button.clicked.connect(open_dialog)
    layout.addWidget(button)
    return widget, line_edit

def create_app_selection_with_flyout_widget(parent_window, dialog_title_text, predefined_apps: dict = None):
    widget = QWidget()
    h_layout = QHBoxLayout(widget)
    h_layout.setContentsMargins(0, 0, 0, 0)
    
    line_edit = QLineEdit() # Create the QLineEdit here to be shared

    flyout_button = QToolButton()
    flyout_button.setText("▼") 
    flyout_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
    app_menu = QMenu(flyout_button)
    flyout_button.setMenu(app_menu)

    if predefined_apps:
        for app_name, app_value_or_action in predefined_apps.items():
            action = app_menu.addAction(app_name)
            if app_name == "Add New..." and callable(app_value_or_action):
                # For "Add New...", the lambda should call parent_window._add_new_app_dialog
                # The parent_window._add_new_app_dialog method itself takes (target_line_edit, app_type_name)
                # So, the lambda created here must provide 'line_edit' (created in this function) as the target.
                action.triggered.connect(lambda checked=False, le=line_edit, title=dialog_title_text: parent_window._add_new_app_dialog(le, title.replace("Select ","").replace(" Application","").replace(" Solution","")))
            elif callable(app_value_or_action): # For other callable actions (though not used in original setup tab for flyouts)
                 action.triggered.connect(app_value_or_action)
            else: # Original behavior for predefined paths, setting the text of 'line_edit'
                action.triggered.connect(lambda checked=False, text=app_value_or_action, le=line_edit: le.setText(text))
                
    browse_button_explicit = QPushButton("Browse")
    def open_browse_dialog_explicit():
        path, _ = QFileDialog.getOpenFileName(parent_window, dialog_title_text)
        if path:
            line_edit.setText(path)
    browse_button_explicit.clicked.connect(open_browse_dialog_explicit)
    
    h_layout.addWidget(flyout_button)
    h_layout.addWidget(line_edit, 1)
    h_layout.addWidget(browse_button_explicit)
    return widget, line_edit # Return the created line_edit

def create_app_selection_with_run_wait_widget(parent_window, dialog_title_text, predefined_apps: dict = None):
    flyout_widget_container, line_edit_ref = create_app_selection_with_flyout_widget(parent_window, dialog_title_text, predefined_apps)
    
    run_wait_checkbox = QCheckBox("Run-Wait")
    run_wait_checkbox.setChecked(True) 
    
    parent_widget = QWidget()
    layout = QHBoxLayout(parent_widget)
    layout.setContentsMargins(0,0,0,0)
    layout.addWidget(flyout_widget_container, 1) 
    layout.addWidget(run_wait_checkbox)
    
    return parent_widget, line_edit_ref, run_wait_checkbox

def create_list_management_widget(parent_window, is_directory_list=True):
    widget = QWidget()
    layout = QHBoxLayout(widget)
    layout.setContentsMargins(0,0,0,0)
    combo_box = QComboBox()
    combo_box.setMinimumWidth(200) 
    layout.addWidget(combo_box, 1)
    add_button = QPushButton("Add")
    remove_button = QPushButton("Remove")
    def add_item():
        dialog_title = "Select Directory to Add" if is_directory_list else "Enter Item to Add" # Changed for non-directory
        path_to_add = ""
        if is_directory_list:
            path_to_add = QFileDialog.getExistingDirectory(parent_window, dialog_title)
        else: 
            # For non-directory lists (like exclude items), better to use QInputDialog for text
            # Defaulting to QFileDialog.getExistingDirectory for now based on original code's usage pattern
            # but this was marked with "Pattern TODO" in original _create_list_management_widget for exclude_items
            # Consider changing this to QInputDialog.getText for non-directory lists if they are not paths.
            path_to_add, ok = QFileDialog.getExistingDirectory(parent_window, "Select Directory to Exclude"), True # Placeholder for ok
            # if ok and text: path_to_add = text (if using QInputDialog)
        if path_to_add: # Ensure path_to_add is not empty
            if combo_box.findText(path_to_add) == -1:
                 combo_box.addItem(path_to_add)
    def remove_item():
        current_index = combo_box.currentIndex()
        if current_index >= 0:
            combo_box.removeItem(current_index)
    add_button.clicked.connect(add_item)
    remove_button.clicked.connect(remove_item)
    layout.addWidget(add_button)
    layout.addWidget(remove_button)
    return widget, combo_box

def create_deployment_path_row_widget(parent_window, setup_qlineedit_to_mirror: QLineEdit):
    """Create a row widget with CEN/LC radio buttons and a path label"""
    row_widget = QWidget()
    row_layout = QHBoxLayout(row_widget)
    row_layout.setContentsMargins(0, 0, 0, 0)

    # Create radio button group
    radio_group = QButtonGroup(row_widget)
    
    # Replace checkboxes with radio buttons
    uoc_radio = QRadioButton("CEN")
    uoc_radio.setToolTip("Use Original Config: If selected, the application will use the path defined in the Setup tab.")
    uoc_radio.setChecked(True)
    
    lc_radio = QRadioButton("LC")
    lc_radio.setToolTip("Launch Conditionally: If selected, this associated application/script will only be launched if certain conditions are met (details TBD).")
    
    # Add radio buttons to the group
    radio_group.addButton(uoc_radio)
    radio_group.addButton(lc_radio)

    path_display_line_edit = QLineEdit()
    path_display_line_edit.setText(setup_qlineedit_to_mirror.text() if setup_qlineedit_to_mirror else "Path not set in Setup")
    path_display_line_edit.setReadOnly(True)
    path_display_line_edit.setToolTip("This path is configured in the Setup tab.")
    
    if setup_qlineedit_to_mirror:
        setup_qlineedit_to_mirror.textChanged.connect(
            lambda text, display_le=path_display_line_edit: display_le.setText(text)
        )

    row_layout.addWidget(uoc_radio)
    row_layout.addWidget(path_display_line_edit, 1)
    row_layout.addWidget(lc_radio)
    
    return row_widget, uoc_radio, path_display_line_edit, lc_radio
