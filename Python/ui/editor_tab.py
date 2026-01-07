from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QLabel,
    QPushButton, QHeaderView, QAbstractItemView, QMenu, QCheckBox, QLineEdit,
    QApplication, QFileDialog, QInputDialog, QMessageBox, QSpinBox
)
import os
import json 
import copy
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor
from Python import constants

class EditorTab(QWidget):
    """Encapsulates the UI and logic for the Editor tab."""

    save_index_requested = pyqtSignal()
    load_index_requested = pyqtSignal()
    delete_indexes_requested = pyqtSignal()
    clear_view_requested = pyqtSignal()
    data_changed = pyqtSignal()

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.table = None
        self.original_data = []
        self.filtered_data = []
        self.current_page = 0
        self.page_size = 75
        self.populate_ui()

    def populate_ui(self):
        """Create and arrange widgets for the editor tab."""
        main_layout = QVBoxLayout(self)

        # --- Search Bar ---
        search_layout = QHBoxLayout()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search games by name...")
        self.search_bar.textChanged.connect(self.filter_table)
        search_layout.addWidget(QLabel("Search:"))
        search_layout.addWidget(self.search_bar)
        
        # Toggle Create Button
        self.toggle_create_button = QPushButton("Toggle Create")
        self.toggle_create_button.clicked.connect(self.toggle_create_column)
        search_layout.addWidget(self.toggle_create_button)

        # Add Game Button
        self.add_game_button = QPushButton("Add Game")
        self.add_game_button.clicked.connect(self.add_game_manually)
        search_layout.addWidget(self.add_game_button)
        main_layout.addLayout(search_layout)

        # --- Table ---
        self.table = QTableWidget()
        # set column count based on EditorCols mapping
        self.table.setColumnCount(max(c.value for c in constants.EditorCols) + 1)
        
        headers = [
            "Create", "Name", "Dir", "SteamID",
            "NameOverride", "opts", "args", "AsAdmin",
            "Mapper", "Wait",
            "Windowing", "Wait", "Win-Exit",
            "Multi-Monitor", "Wait",
            "Hide TB",
            "MM Game", "MM Desktop",
            "Player 1", "Player 2", "MediaCenter",
            "OnStart", "Wait",
            "PreQuit", "Wait",
            "Pre1", "Wait",
            "Post1", "Wait",
            "Pre2", "Wait",
            "Post2", "Wait",
            "Pre3", "Wait",
            "Post3", "Wait",
            "Kill List"
        ]
        self.table.setHorizontalHeaderLabels(headers)

        tooltips = [
            "Include this game in the creation process", "Executable name", "Game directory", "Steam AppID",
            "Display name for the launcher", "Additional launch options", "Command line arguments for the game", "Run game as administrator",
            "Path to controller mapper profile/executable", "Wait for Controller Mapper to finish?",
            "Path to Borderless Gaming executable", "Wait for Borderless Gaming to finish?", "Terminate Borderless Gaming when game exits",
            "Path to Multi-Monitor tool", "Wait for Multi-Monitor tool?",
            "Hide Windows Taskbar while game is running",
            "Monitor configuration for Game", "Monitor configuration for Desktop",
            "Controller profile for Player 1", "Controller profile for Player 2", "Controller profile for Media Center",
            "App to run immediately after game launch", "Wait for this app?",
            "App to run just before game exits", "Wait for this app?",
            "Pre-launch script 1", "Wait for Pre1?",
            "Post-launch script 1", "Wait for Post1?",
            "Pre-launch script 2", "Wait for Pre2?",
            "Post-launch script 2", "Wait for Post2?",
            "Pre-launch script 3", "Wait for Pre3?",
            "Post-launch script 3", "Wait for Post3?",
            "Comma-separated list of processes to kill (Checked = Enabled)"
        ]
        for i, tooltip in enumerate(tooltips):
            item = self.table.horizontalHeaderItem(i)
            if item:
                item.setToolTip(tooltip)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

        # Shorten width for Enabled (En) and Run/Wait (Rw) columns to save space
        try:
            rw_columns = [constants.EditorCols.CM_RUN_WAIT.value, constants.EditorCols.BW_RUN_WAIT.value,
                          constants.EditorCols.MM_RUN_WAIT.value, constants.EditorCols.JA_RUN_WAIT.value,
                          constants.EditorCols.JB_RUN_WAIT.value, constants.EditorCols.PRE1_RUN_WAIT.value,
                          constants.EditorCols.POST1_RUN_WAIT.value, constants.EditorCols.PRE2_RUN_WAIT.value,
                          constants.EditorCols.POST2_RUN_WAIT.value, constants.EditorCols.PRE3_RUN_WAIT.value,
                          constants.EditorCols.POST3_RUN_WAIT.value]

            for col in rw_columns:
                # Automatically resize Wait columns to fit content
                header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
            
            self.table.setColumnWidth(constants.EditorCols.WIN_EXIT.value, 56)
            self.table.setColumnWidth(constants.EditorCols.RUN_AS_ADMIN.value, 60)

            # Reduce width of opts, args, and Directory by 80%
            shrink_cols = [constants.EditorCols.DIRECTORY.value, constants.EditorCols.OPTIONS.value, constants.EditorCols.ARGUMENTS.value]
            for col in shrink_cols:
                self.table.setColumnWidth(col, 40)
        except Exception:
            pass
        header.setStretchLastSection(False)
        header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        header.customContextMenuRequested.connect(self.on_header_context_menu)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.AllEditTriggers)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        main_layout.addWidget(self.table)

        # --- Pagination ---
        pagination_layout = QHBoxLayout()
        self.prev_page_button = QPushButton("< Prev")
        self.prev_page_button.clicked.connect(self.prev_page)
        
        self.page_input = QSpinBox()
        self.page_input.setMinimum(1)
        self.page_input.setKeyboardTracking(False)
        self.page_input.valueChanged.connect(self.go_to_page)
        
        self.next_page_button = QPushButton("Next >")
        self.next_page_button.clicked.connect(self.next_page)
        self.page_label = QLabel("of 1")
        pagination_layout.addWidget(self.prev_page_button)
        pagination_layout.addWidget(QLabel("Page:"))
        pagination_layout.addWidget(self.page_input)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.next_page_button)
        main_layout.addLayout(pagination_layout)

        # --- Buttons ---
        buttons_layout = QHBoxLayout()
        self.save_button = QPushButton("Save Index")
        self.load_button = QPushButton("Load Index")
        self.delete_button = QPushButton("Delete Indexes")
        self.clear_button = QPushButton("Clear View")
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.load_button)
        buttons_layout.addWidget(self.delete_button)
        buttons_layout.addWidget(self.clear_button)
        main_layout.addLayout(buttons_layout)

        # --- Connect Signals ---
        self.save_button.clicked.connect(self.save_index_requested.emit)
        self.load_button.clicked.connect(self.load_index_requested.emit)
        self.delete_button.clicked.connect(self.delete_indexes_requested.emit)
        self.clear_button.clicked.connect(self.clear_view_requested.emit)

        self.table.customContextMenuRequested.connect(self.on_context_menu)
        self.table.cellClicked.connect(self.on_cell_clicked)
        self.table.itemChanged.connect(self.on_item_changed)

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh_view()

    def next_page(self):
        max_page = max(0, (len(self.filtered_data) - 1) // self.page_size)
        if self.current_page < max_page:
            self.current_page += 1
            self.refresh_view()

    def go_to_page(self, value):
        new_page = value - 1
        max_page = max(0, (len(self.filtered_data) - 1) // self.page_size)
        if 0 <= new_page <= max_page:
            self.current_page = new_page
            self.refresh_view()
            self.page_input.setValue(self.current_page + 1)

    def refresh_view(self):
        """Refresh the table to show the current page of data."""
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        
        start_index = self.current_page * self.page_size
        end_index = min(start_index + self.page_size, len(self.filtered_data))
        
        for i in range(start_index, end_index):
            row_num = self.table.rowCount()
            self.table.insertRow(row_num)
            self._populate_row(row_num, self.filtered_data[i])
            
        self.table.blockSignals(False)
        
        # Update pagination controls
        total_pages = max(1, (len(self.filtered_data) + self.page_size - 1) // self.page_size)
        
        self.page_input.blockSignals(True)
        self.page_input.setMaximum(total_pages)
        self.page_input.setValue(self.current_page + 1)
        self.page_input.blockSignals(False)
        
        self.page_label.setText(f"of {total_pages} (Total: {len(self.filtered_data)})")
        self.prev_page_button.setEnabled(self.current_page > 0)
        self.next_page_button.setEnabled(self.current_page < total_pages - 1)
        self.data_changed.emit()

    def filter_table(self, text):
        """Filter table rows based on game name."""
        text = text.lower()
        if not text:
            self.filtered_data = self.original_data
        else:
            self.filtered_data = [g for g in self.original_data if text in g.get('name', '').lower() or text in g.get('name_override', '').lower()]
        
        self.current_page = 0
        self.refresh_view()

    def toggle_create_column(self):
        """Toggle all checkboxes in the Create column based on visibility."""
        # Check if all visible items are checked
        all_checked = True
        for row in range(self.table.rowCount()):
            if not self.table.isRowHidden(row):
                real_index = (self.current_page * self.page_size) + row
                if real_index < len(self.filtered_data) and not self.filtered_data[real_index].get('create', False):
                    all_checked = False
                    break
        
        target_state = not all_checked
        
        for row in range(self.table.rowCount()):
            real_index = (self.current_page * self.page_size) + row
            if real_index < len(self.filtered_data):
                self.filtered_data[real_index]['create'] = target_state
                # Update widget visually
                self._update_widget_state(row, constants.EditorCols.INCLUDE.value, target_state)
        self.data_changed.emit()

    def add_game_manually(self):
        """Open file dialog to add a game manually."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Game Executable", "", "Executables (*.exe);;All Files (*)"
        )
        if not file_path:
            return

        filename = os.path.basename(file_path)
        directory = os.path.dirname(file_path)
        
        # Default values
        name_override = os.path.splitext(filename)[0]
        steam_id = 'NOT_FOUND_IN_DATA'

        # Attempt to detect Steam AppID
        try:
            from Python.ui.name_processor import NameProcessor
            from Python.ui.name_utils import replace_illegal_chars

            # Ensure steam index is loaded
            if not self.main_window.steam_cache_manager.normalized_steam_index:
                self.main_window.steam_cache_manager.load_normalized_steam_index()

            # Initialize NameProcessor
            release_groups = getattr(self.main_window, 'release_groups_set', set())
            exclude_exe = getattr(self.main_window, 'exclude_exe_set', set())
            name_processor = NameProcessor(release_groups, exclude_exe)

            # Process name
            clean_name = name_processor.get_display_name(name_override)
            match_name = name_processor.get_match_name(clean_name)
            
            # Lookup
            if self.main_window.config.enable_name_matching:
                match_data = self.main_window.steam_cache_manager.normalized_steam_index.get(match_name)
                if match_data:
                    steam_name = match_data.get("name", "")
                    found_id = match_data.get("id", "")
                    
                    if found_id:
                        steam_id = found_id
                    
                    if steam_name:
                        # Clean steam name for override
                        clean_steam_name = replace_illegal_chars(steam_name, " - ")
                        while "  " in clean_steam_name: clean_steam_name = clean_steam_name.replace("  ", " ")
                        while "- -" in clean_steam_name: clean_steam_name = clean_steam_name.replace("- -", " - ")
                        name_override = clean_steam_name.strip()
                    else:
                        name_override = clean_name
                else:
                    name_override = clean_name
            else:
                name_override = clean_name

        except Exception as e:
            print(f"Error detecting Steam AppID: {e}")

        game_data = {
            'create': True,
            'name': filename,
            'directory': directory,
            'name_override': name_override,
            'steam_id': steam_id
        }
        
        self.original_data.append(copy.deepcopy(game_data))
        self.filter_table(self.search_bar.text()) # Re-filter and refresh
        # Scroll to bottom of current view if added
        row = self.table.rowCount() - 1
        self.table.scrollToItem(self.table.item(row, 0))
        self.main_window._on_editor_table_edited(None)

    def on_header_context_menu(self, position):
        """Handle context menu for column headers."""
        index = self.table.horizontalHeader().logicalIndexAt(position)
        if index < 0:
            return

        menu = QMenu(self)
        select_col_action = menu.addAction("Select Column")
        
        action = menu.exec(self.table.horizontalHeader().mapToGlobal(position))
        
        if action == select_col_action:
            self.table.selectColumn(index)

    def on_context_menu(self, position):
        """Create and display custom context menu for the table."""
        row = self.table.rowAt(position.y())
        col = self.table.columnAt(position.x())
        
        if row < 0 or col < 0:
            return

        menu = QMenu(self)
        
        # Toggle Create Action
        toggle_create_action = menu.addAction("Toggle 'Create' for Selected")
        toggle_create_action.triggered.connect(self.toggle_create_for_selection)
        
        # Clone Game Action
        clone_action = menu.addAction("Clone Game")
        clone_action.triggered.connect(lambda: self.clone_game(row))

        # Open Game.ini Action
        open_ini_action = menu.addAction("Open Game.ini")
        open_ini_action.triggered.connect(lambda: self.open_game_ini(row))

        # Open Profile Folder Action
        open_profile_action = menu.addAction("Open Profile Folder")
        open_profile_action.triggered.connect(lambda: self.open_profile_folder(row))

        menu.addSeparator()

        # Edit
        edit_action = menu.addAction("Edit this Field")
        edit_action.triggered.connect(lambda: self.edit_cell(row, col))
        
        # Select Row
        select_row_action = menu.addAction("Select Row")
        select_row_action.triggered.connect(lambda: self.table.selectRow(row))
        
        menu.addSeparator()
        select_all_action = menu.addAction("Select All")
        select_all_action.triggered.connect(self.table.selectAll)
        deselect_all_action = menu.addAction("Deselect All")
        deselect_all_action.triggered.connect(self.table.clearSelection)
        
        menu.addSeparator()
        
        # Copy/Paste
        copy_action = menu.addAction("Copy")
        copy_action.triggered.connect(lambda: self.copy_cell(row, col))
        
        paste_action = menu.addAction("Paste")
        paste_action.triggered.connect(lambda: self.paste_cell(row, col))
        
        if col == constants.EditorCols.STEAMID.value:
            search_steam_action = menu.addAction("Search Steam AppID")
            search_steam_action.triggered.connect(lambda: self.search_steam_id(row))
            
        if col == constants.EditorCols.KILL_LIST.value:
            self._add_kill_list_menu(menu, row)

        menu.addSeparator()

        reset_row_action = menu.addAction("Reset Row")
        reset_row_action.triggered.connect(lambda: self.reset_row(row))

        menu.addSeparator()
        
        # Check column range for "Apply to Selected"
        if constants.EditorCols.ARGUMENTS.value < col < constants.EditorCols.KILL_LIST.value:
            apply_action = menu.addAction("Propagate selection to column")
            apply_action.triggered.connect(lambda: self.apply_cell_value_to_selection(row, col))
            
        if not menu.isEmpty():
            menu.exec(self.table.viewport().mapToGlobal(position))

    def clone_game(self, row):
        """Clone the game at the specified row."""
        real_index = (self.current_page * self.page_size) + row
        if real_index < len(self.filtered_data):
            game_to_clone = self.filtered_data[real_index]
            new_game = copy.deepcopy(game_to_clone)
            
            # Modify name to indicate clone
            new_game['name_override'] = f"{new_game.get('name_override', '')} (Copy)"
            
            # Insert after the current item in original_data
            try:
                original_index = self.original_data.index(game_to_clone)
                self.original_data.insert(original_index + 1, new_game)
            except ValueError:
                self.original_data.append(new_game)
                
            # Refresh view
            self.filter_table(self.search_bar.text())
            self.main_window._on_editor_table_edited(None)

    def open_game_ini(self, row):
        """Open the Game.ini file for the selected game."""
        real_index = (self.current_page * self.page_size) + row
        if real_index < len(self.filtered_data):
            game_data = self.filtered_data[real_index]
            
            from Python.ui.name_utils import make_safe_filename
            safe_name = make_safe_filename(game_data.get('name_override', ''))
            if not safe_name:
                 safe_name = make_safe_filename(game_data.get('name', ''))
            
            profiles_dir = self.main_window.config.profiles_dir
            ini_path = os.path.join(profiles_dir, safe_name, "Game.ini")
            
            if os.path.exists(ini_path):
                os.startfile(ini_path)
            else:
                QMessageBox.warning(self, "File Not Found", f"Game.ini not found at:\n{ini_path}\n\nHas the game been created yet?")

    def open_profile_folder(self, row):
        """Open the profile folder for the selected game."""
        real_index = (self.current_page * self.page_size) + row
        if real_index < len(self.filtered_data):
            game_data = self.filtered_data[real_index]
            
            from Python.ui.name_utils import make_safe_filename
            safe_name = make_safe_filename(game_data.get('name_override', ''))
            if not safe_name:
                 safe_name = make_safe_filename(game_data.get('name', ''))
            
            profiles_dir = self.main_window.config.profiles_dir
            profile_path = os.path.join(profiles_dir, safe_name)
            
            if os.path.exists(profile_path):
                os.startfile(profile_path)
            else:
                QMessageBox.warning(self, "Folder Not Found", f"Profile folder not found at:\n{profile_path}\n\nHas the game been created yet?")

    def toggle_create_for_selection(self):
        """Toggle the 'create' status for all selected rows."""
        selected_rows = set()
        for range_ in self.table.selectedRanges():
            for r in range(range_.topRow(), range_.bottomRow() + 1):
                selected_rows.add(r)
        
        if not selected_rows:
            return

        # Determine target state: if any are unchecked, check all. Otherwise uncheck all.
        target_state = False
        for row in selected_rows:
            real_index = (self.current_page * self.page_size) + row
            if real_index < len(self.filtered_data):
                if not self.filtered_data[real_index].get('create', False):
                    target_state = True
                    break
        
        for row in selected_rows:
            real_index = (self.current_page * self.page_size) + row
            if real_index < len(self.filtered_data):
                self.filtered_data[real_index]['create'] = target_state
                self._update_widget_state(row, constants.EditorCols.INCLUDE.value, target_state)
        
        self.data_changed.emit()

    def edit_cell(self, row, col):
        item = self.table.item(row, col)
        if item:
            self.table.editItem(item)

    def copy_cell(self, row, col):
        state = self._get_cell_state(row, col)
        if state:
            try:
                QApplication.clipboard().setText(json.dumps(state))
            except Exception:
                pass

    def paste_cell(self, row, col):
        text = QApplication.clipboard().text()
        if not text: return
        
        try:
            # Try to parse as state JSON
            state = json.loads(text)
            if isinstance(state, dict) and 'type' in state:
                self._set_cell_state(row, col, state)
                self.main_window._on_editor_table_edited(None)
                return
        except Exception:
            pass
            
        # Fallback: Paste as text if cell supports it
        item = self.table.item(row, col)
        if item:
            item.setText(text)
            self.main_window._on_editor_table_edited(None)

    def search_steam_id(self, row):
        """Manually search for a Steam AppID."""
        name_item = self.table.item(row, constants.EditorCols.NAME_OVERRIDE.value)
        if not name_item or not name_item.text():
            name_item = self.table.item(row, constants.EditorCols.NAME.value)
        
        current_name = name_item.text() if name_item else ""
        
        search_term, ok = QInputDialog.getText(self, "Search Steam AppID", "Enter game name:", text=current_name)
        
        if ok and search_term:
            if not self.main_window.steam_cache_manager.normalized_steam_index:
                self.main_window.steam_cache_manager.load_normalized_steam_index()
            
            try:
                from Python.ui.name_processor import NameProcessor
                release_groups = getattr(self.main_window, 'release_groups_set', set())
                exclude_exe = getattr(self.main_window, 'exclude_exe_set', set())
                name_processor = NameProcessor(release_groups, exclude_exe)
                
                match_name = name_processor.get_match_name(search_term)
                match_data = self.main_window.steam_cache_manager.normalized_steam_index.get(match_name)
                
                if match_data:
                    steam_id = match_data.get("id")
                    steam_name = match_data.get("name")
                    confirm = QMessageBox.question(self, "Steam AppID Found", f"Found: {steam_name}\nAppID: {steam_id}\n\nApply this ID?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                    if confirm == QMessageBox.StandardButton.Yes:
                        self.table.setItem(row, constants.EditorCols.STEAMID.value, QTableWidgetItem(str(steam_id)))
                        self.main_window._on_editor_table_edited(None)
                else:
                    QMessageBox.information(self, "Not Found", f"No Steam game found matching '{search_term}'")
            except Exception as e:
                print(f"Error searching Steam ID: {e}")

    def _add_kill_list_menu(self, menu, row):
        """Add context menu items for Kill List."""
        kp_menu = menu.addMenu("Add Common Process")
        
        procs = []
        if os.path.exists(constants.KILLPROCS_SET):
            try:
                with open(constants.KILLPROCS_SET, 'r') as f:
                    procs = [line.strip() for line in f if line.strip()]
            except Exception:
                pass
        
        if not procs:
            kp_menu.addAction("No processes found").setEnabled(False)
            return

        for proc in procs:
            action = kp_menu.addAction(proc)
            action.triggered.connect(lambda checked, p=proc, r=row: self.append_kill_proc(r, p))

    def append_kill_proc(self, row, proc):
        """Append a process to the kill list."""
        item = self.table.item(row, constants.EditorCols.KILL_LIST.value)
        current_text = item.text() if item else ""
        
        # Avoid duplicates if possible, or just append
        current_list = [p.strip() for p in current_text.split(',')] if current_text else []
        if proc not in current_list:
            current_list.append(proc)
            new_text = ",".join(current_list)
            if not item:
                item = QTableWidgetItem()
                self.table.setItem(row, constants.EditorCols.KILL_LIST.value, item)
            item.setText(new_text)
            self.main_window._on_editor_table_edited(None)

    def reset_row(self, row):
        """Reset the row to its original state."""
        if 0 <= row < len(self.original_data):
            reply = QMessageBox.question(
                self, "Confirm Reset",
                "Are you sure you want to reset this row to its original state?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

            game_data = self.original_data[row]
            self._populate_row(row, copy.deepcopy(game_data))
            self.main_window._on_editor_table_edited(None)

    def on_cell_clicked(self, row, column):
        """Handle left click on a cell."""
        self.main_window._on_editor_table_cell_left_click(row, column)

    def on_item_changed(self, item):
        """Handle changes to table items."""
        if not self.table.signalsBlocked():
            self._sync_cell_to_data(item.row(), item.column())
        self.main_window._on_editor_table_edited(item)
        self.data_changed.emit()

    def _create_checkbox_widget(self, checked: bool, row: int, col: int) -> QWidget:
        """Create a centered checkbox widget for table cells."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        checkbox = QCheckBox()
        checkbox.setChecked(checked)
        checkbox.stateChanged.connect(lambda state: self._on_checkbox_changed(row, col, state))
        layout.addWidget(checkbox)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        return widget

    def _create_merged_path_widget(self, enabled: bool, path_text: str, overwrite: bool, row: int, col: int) -> QWidget:
        """Create a merged widget with Enabled checkbox, Path label, and Overwrite checkbox."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setSpacing(6)
        
        cb_enabled = QCheckBox()
        cb_enabled.setChecked(enabled)
        cb_enabled.setToolTip("Enable")
        cb_enabled.stateChanged.connect(lambda state: self._on_merged_widget_changed(row, col))
        
        line_edit = QLineEdit(path_text)
        line_edit.setToolTip(path_text)
        line_edit.textChanged.connect(lambda text: self._on_merged_widget_changed(row, col))
        
        cb_overwrite = QCheckBox()
        cb_overwrite.setChecked(overwrite)
        cb_overwrite.setToolTip("Overwrite")
        cb_overwrite.stateChanged.connect(lambda state: self._on_merged_widget_changed(row, col))
        
        layout.addWidget(cb_enabled)
        layout.addWidget(line_edit, 1)
        layout.addWidget(cb_overwrite)
        
        return widget

    def _on_checkbox_changed(self, row, col, state):
        self._sync_cell_to_data(row, col)
        self.data_changed.emit()

    def _on_merged_widget_changed(self, row, col):
        self._sync_cell_to_data(row, col)
        self.data_changed.emit()

    def _sync_cell_to_data(self, row, col):
        """Update the underlying data model from the table widget."""
        real_index = (self.current_page * self.page_size) + row
        if real_index >= len(self.filtered_data):
            return

        game = self.filtered_data[real_index]
        
        # Map column to data key
        if col == constants.EditorCols.INCLUDE.value:
            game['create'] = self._get_checkbox_value(row, col)
        elif col == constants.EditorCols.NAME.value:
            item = self.table.item(row, col)
            game['name'] = item.text() if item else ""
        elif col == constants.EditorCols.DIRECTORY.value:
            item = self.table.item(row, col)
            game['directory'] = item.text() if item else ""
        elif col == constants.EditorCols.STEAMID.value:
            item = self.table.item(row, col)
            game['steam_id'] = item.text() if item else ""
        elif col == constants.EditorCols.NAME_OVERRIDE.value:
            item = self.table.item(row, col)
            game['name_override'] = item.text() if item else ""
        elif col == constants.EditorCols.OPTIONS.value:
            item = self.table.item(row, col)
            game['options'] = item.text() if item else ""
        elif col == constants.EditorCols.ARGUMENTS.value:
            item = self.table.item(row, col)
            game['arguments'] = item.text() if item else ""
        elif col == constants.EditorCols.RUN_AS_ADMIN.value:
            game['run_as_admin'] = self._get_checkbox_value(row, col)
        elif col == constants.EditorCols.CM_PATH.value:
            en, path, ov = self._get_merged_path_data(row, col)
            game['controller_mapper_enabled'] = en
            game['controller_mapper_path'] = path
            game['controller_mapper_overwrite'] = ov
        elif col == constants.EditorCols.CM_RUN_WAIT.value:
            game['controller_mapper_run_wait'] = self._get_checkbox_value(row, col)
        elif col == constants.EditorCols.BW_PATH.value:
            en, path, ov = self._get_merged_path_data(row, col)
            game['borderless_windowing_enabled'] = en
            game['borderless_windowing_path'] = path
            game['borderless_windowing_overwrite'] = ov
        elif col == constants.EditorCols.BW_RUN_WAIT.value:
            game['borderless_windowing_run_wait'] = self._get_checkbox_value(row, col)
        elif col == constants.EditorCols.WIN_EXIT.value:
            game['terminate_borderless_on_exit'] = self._get_checkbox_value(row, col)
        elif col == constants.EditorCols.MM_PATH.value:
            en, path, ov = self._get_merged_path_data(row, col)
            game['multi_monitor_app_enabled'] = en
            game['multi_monitor_app_path'] = path
            game['multi_monitor_app_overwrite'] = ov
        elif col == constants.EditorCols.MM_RUN_WAIT.value:
            game['multi_monitor_app_run_wait'] = self._get_checkbox_value(row, col)
        elif col == constants.EditorCols.HIDE_TASKBAR.value:
            game['hide_taskbar'] = self._get_checkbox_value(row, col)
        elif col == constants.EditorCols.MM_GAME_PROFILE.value:
            en, path, ov = self._get_merged_path_data(row, col)
            game['mm_game_profile_enabled'] = en
            game['mm_game_profile'] = path
            game['mm_game_profile_overwrite'] = ov
        elif col == constants.EditorCols.MM_DESKTOP_PROFILE.value:
            en, path, ov = self._get_merged_path_data(row, col)
            game['mm_desktop_profile_enabled'] = en
            game['mm_desktop_profile'] = path
            game['mm_desktop_profile_overwrite'] = ov
        elif col == constants.EditorCols.PLAYER1_PROFILE.value:
            en, path, ov = self._get_merged_path_data(row, col)
            game['player1_profile_enabled'] = en
            game['player1_profile'] = path
            game['player1_profile_overwrite'] = ov
        elif col == constants.EditorCols.PLAYER2_PROFILE.value:
            en, path, ov = self._get_merged_path_data(row, col)
            game['player2_profile_enabled'] = en
            game['player2_profile'] = path
            game['player2_profile_overwrite'] = ov
        elif col == constants.EditorCols.MEDIACENTER_PROFILE.value:
            en, path, ov = self._get_merged_path_data(row, col)
            game['mediacenter_profile_enabled'] = en
            game['mediacenter_profile'] = path
            game['mediacenter_profile_overwrite'] = ov
        elif col == constants.EditorCols.JA_PATH.value:
            en, path, ov = self._get_merged_path_data(row, col)
            game['just_after_launch_enabled'] = en
            game['just_after_launch_path'] = path
            game['just_after_launch_overwrite'] = ov
        elif col == constants.EditorCols.JA_RUN_WAIT.value:
            game['just_after_launch_run_wait'] = self._get_checkbox_value(row, col)
        elif col == constants.EditorCols.JB_PATH.value:
            en, path, ov = self._get_merged_path_data(row, col)
            game['just_before_exit_enabled'] = en
            game['just_before_exit_path'] = path
            game['just_before_exit_overwrite'] = ov
        elif col == constants.EditorCols.JB_RUN_WAIT.value:
            game['just_before_exit_run_wait'] = self._get_checkbox_value(row, col)
        elif col == constants.EditorCols.PRE1_PATH.value:
            en, path, ov = self._get_merged_path_data(row, col)
            game['pre_1_enabled'] = en
            game['pre1_path'] = path
            game['pre_1_overwrite'] = ov
        elif col == constants.EditorCols.PRE1_RUN_WAIT.value:
            game['pre_1_run_wait'] = self._get_checkbox_value(row, col)
        elif col == constants.EditorCols.POST1_PATH.value:
            en, path, ov = self._get_merged_path_data(row, col)
            game['post_1_enabled'] = en
            game['post1_path'] = path
            game['post_1_overwrite'] = ov
        elif col == constants.EditorCols.POST1_RUN_WAIT.value:
            game['post_1_run_wait'] = self._get_checkbox_value(row, col)
        elif col == constants.EditorCols.PRE2_PATH.value:
            en, path, ov = self._get_merged_path_data(row, col)
            game['pre_2_enabled'] = en
            game['pre2_path'] = path
            game['pre_2_overwrite'] = ov
        elif col == constants.EditorCols.PRE2_RUN_WAIT.value:
            game['pre_2_run_wait'] = self._get_checkbox_value(row, col)
        elif col == constants.EditorCols.POST2_PATH.value:
            en, path, ov = self._get_merged_path_data(row, col)
            game['post_2_enabled'] = en
            game['post2_path'] = path
            game['post_2_overwrite'] = ov
        elif col == constants.EditorCols.POST2_RUN_WAIT.value:
            game['post_2_run_wait'] = self._get_checkbox_value(row, col)
        elif col == constants.EditorCols.PRE3_PATH.value:
            en, path, ov = self._get_merged_path_data(row, col)
            game['pre_3_enabled'] = en
            game['pre3_path'] = path
            game['pre_3_overwrite'] = ov
        elif col == constants.EditorCols.PRE3_RUN_WAIT.value:
            game['pre_3_run_wait'] = self._get_checkbox_value(row, col)
        elif col == constants.EditorCols.POST3_PATH.value:
            en, path, ov = self._get_merged_path_data(row, col)
            game['post_3_enabled'] = en
            game['post3_path'] = path
            game['post_3_overwrite'] = ov
        elif col == constants.EditorCols.POST3_RUN_WAIT.value:
            game['post_3_run_wait'] = self._get_checkbox_value(row, col)
        elif col == constants.EditorCols.KILL_LIST.value:
            item = self.table.item(row, col)
            if item:
                game['kill_list_enabled'] = (item.checkState() == Qt.CheckState.Checked)
                game['kill_list'] = item.text()

    def _update_widget_state(self, row, col, value):
        """Update a widget's visual state without triggering data sync."""
        self.table.blockSignals(True)
        if col == constants.EditorCols.INCLUDE.value:
            widget = self.table.cellWidget(row, col)
            if widget:
                cb = widget.findChild(QCheckBox)
                if cb: cb.setChecked(value)
        self.table.blockSignals(False)

    def _get_checkbox_value(self, row: int, col: int) -> bool:
        """Get checkbox value from a cell widget."""
        widget = self.table.cellWidget(row, col)
        if widget:
            checkbox = widget.findChild(QCheckBox)
            if checkbox:
                return checkbox.isChecked()
        return False

    def _get_merged_path_data(self, row: int, col: int):
        """Extract enabled, path, and overwrite from a merged widget."""
        widget = self.table.cellWidget(row, col)
        if widget:
            cbs = widget.findChildren(QCheckBox)
            enabled = cbs[0].isChecked() if len(cbs) > 0 else False
            overwrite = cbs[1].isChecked() if len(cbs) > 1 else False
            le = widget.findChild(QLineEdit)
            path = le.text() if le else ""
            return enabled, path, overwrite
        return False, "", False

    def _get_propagation_symbol_and_run_wait(self, config_key):
        """Get propagation status symbol (< or >) and default run_wait state from config"""
        config = self.main_window.config
        # Get the propagation mode (CEN or LC)
        mode = config.deployment_path_modes.get(config_key, 'CEN')
        symbol = '<' if mode == 'CEN' else '>'
        
        # Get the run_wait default state
        run_wait_key = f"{config_key}_run_wait"
        run_wait = config.run_wait_states.get(run_wait_key, False)
        
        return symbol, run_wait

    def populate_from_data(self, data):
        """Populate the table with data."""
        if not data:
            return

        self.original_data = [copy.deepcopy(game) for game in data]
        self.filtered_data = self.original_data
        self.current_page = 0
        self.refresh_view()

    def _populate_row(self, row_num, game):
        """Populate a single row with game data."""
        self.table.blockSignals(True) # Block signals during population
        
        def get_path_display(key, config_key):
            val = game.get(key, '')
            if not val: return ""
            if val.startswith('> ') or val.startswith('< '):
                return val
            symbol, _ = self._get_propagation_symbol_and_run_wait(config_key)
            return f"{symbol} {val.lstrip('<> ')}"

        # Create (CheckBox) - col INCLUDE
        self.table.setCellWidget(row_num, constants.EditorCols.INCLUDE.value, self._create_checkbox_widget(game.get('create', False), row_num, constants.EditorCols.INCLUDE.value))

        # Name (uneditable) - col NAME
        name_item = QTableWidgetItem(game.get('name', ''))
        name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row_num, constants.EditorCols.NAME.value, name_item)

        # Directory (uneditable) - col DIRECTORY
        directory_path = game.get('directory', '')
        dir_item = QTableWidgetItem(directory_path)
        dir_item.setFlags(dir_item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Make it uneditable
        dir_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.table.setItem(row_num, constants.EditorCols.DIRECTORY.value, dir_item)

        # SteamID - col STEAMID
        steam_id_value = game.get('steam_id', 'NOT_FOUND_IN_DATA')
        self.table.setItem(row_num, constants.EditorCols.STEAMID.value, QTableWidgetItem(str(steam_id_value)))

        # NameOverride - col NAME_OVERRIDE
        self.table.setItem(row_num, constants.EditorCols.NAME_OVERRIDE.value, QTableWidgetItem(game.get('name_override', '')))

        # Options - col OPTIONS
        self.table.setItem(row_num, constants.EditorCols.OPTIONS.value, QTableWidgetItem(game.get('options', '')))

        # Arguments - col ARGUMENTS
        self.table.setItem(row_num, constants.EditorCols.ARGUMENTS.value, QTableWidgetItem(game.get('arguments', '')))

        # RunAsAdmin (CheckBox) - col RUN_AS_ADMIN
        self.table.setCellWidget(row_num, constants.EditorCols.RUN_AS_ADMIN.value, self._create_checkbox_widget(game.get('run_as_admin', False), row_num, constants.EditorCols.RUN_AS_ADMIN.value))

        # Controller Mapper (CheckBox, Path with symbol, RunWait)
        # Merged widget for Path column
        cm_symbol, cm_run_wait = self._get_propagation_symbol_and_run_wait('controller_mapper_path')
        cm_path = f"{cm_symbol} {game.get('controller_mapper_path', '').lstrip('<> ')}"
        self.table.setCellWidget(row_num, constants.EditorCols.CM_PATH.value, self._create_merged_path_widget(game.get('controller_mapper_enabled', True), cm_path, game.get('controller_mapper_overwrite', True), row_num, constants.EditorCols.CM_PATH.value))
        self.table.setCellWidget(row_num, constants.EditorCols.CM_RUN_WAIT.value, self._create_checkbox_widget(game.get('controller_mapper_run_wait', cm_run_wait), row_num, constants.EditorCols.CM_RUN_WAIT.value))

        # Borderless Windowing (CheckBox, Path with symbol, RunWait)
        bw_symbol, bw_run_wait = self._get_propagation_symbol_and_run_wait('borderless_gaming_path')
        bw_path = f"{bw_symbol} {game.get('borderless_windowing_path', '').lstrip('<> ')}"
        self.table.setCellWidget(row_num, constants.EditorCols.BW_PATH.value, self._create_merged_path_widget(game.get('borderless_windowing_enabled', True), bw_path, game.get('borderless_windowing_overwrite', True), row_num, constants.EditorCols.BW_PATH.value))
        self.table.setCellWidget(row_num, constants.EditorCols.BW_RUN_WAIT.value, self._create_checkbox_widget(game.get('borderless_windowing_run_wait', bw_run_wait), row_num, constants.EditorCols.BW_RUN_WAIT.value))
        
        # Win-Exit
        self.table.setCellWidget(row_num, constants.EditorCols.WIN_EXIT.value, self._create_checkbox_widget(game.get('terminate_borderless_on_exit', self.main_window.config.terminate_borderless_on_exit), row_num, constants.EditorCols.WIN_EXIT.value))

        # Multi-monitor App (CheckBox, Path with symbol, RunWait)
        mm_symbol, mm_run_wait = self._get_propagation_symbol_and_run_wait('multi_monitor_tool_path')
        mm_path = f"{mm_symbol} {game.get('multi_monitor_app_path', '').lstrip('<> ')}"
        self.table.setCellWidget(row_num, constants.EditorCols.MM_PATH.value, self._create_merged_path_widget(game.get('multi_monitor_app_enabled', True), mm_path, game.get('multi_monitor_app_overwrite', True), row_num, constants.EditorCols.MM_PATH.value))
        self.table.setCellWidget(row_num, constants.EditorCols.MM_RUN_WAIT.value, self._create_checkbox_widget(game.get('multi_monitor_app_run_wait', mm_run_wait), row_num, constants.EditorCols.MM_RUN_WAIT.value))

        # Hide Taskbar (CheckBox)
        self.table.setCellWidget(row_num, constants.EditorCols.HIDE_TASKBAR.value, self._create_checkbox_widget(game.get('hide_taskbar', False), row_num, constants.EditorCols.HIDE_TASKBAR.value))

        # Profiles with propagation symbols
        mm_game_profile = get_path_display('mm_game_profile', 'multimonitor_gaming_path')
        self.table.setCellWidget(row_num, constants.EditorCols.MM_GAME_PROFILE.value, self._create_merged_path_widget(game.get('mm_game_profile_enabled', True), mm_game_profile, game.get('mm_game_profile_overwrite', True), row_num, constants.EditorCols.MM_GAME_PROFILE.value))
        
        mm_desktop_profile = get_path_display('mm_desktop_profile', 'multimonitor_media_path')
        self.table.setCellWidget(row_num, constants.EditorCols.MM_DESKTOP_PROFILE.value, self._create_merged_path_widget(game.get('mm_desktop_profile_enabled', True), mm_desktop_profile, game.get('mm_desktop_profile_overwrite', True), row_num, constants.EditorCols.MM_DESKTOP_PROFILE.value))
        
        player1_profile = get_path_display('player1_profile', 'p1_profile_path')
        self.table.setCellWidget(row_num, constants.EditorCols.PLAYER1_PROFILE.value, self._create_merged_path_widget(game.get('player1_profile_enabled', True), player1_profile, game.get('player1_profile_overwrite', True), row_num, constants.EditorCols.PLAYER1_PROFILE.value))
        
        player2_profile = get_path_display('player2_profile', 'p2_profile_path')
        self.table.setCellWidget(row_num, constants.EditorCols.PLAYER2_PROFILE.value, self._create_merged_path_widget(game.get('player2_profile_enabled', True), player2_profile, game.get('player2_profile_overwrite', True), row_num, constants.EditorCols.PLAYER2_PROFILE.value))
        
        mediacenter_profile = get_path_display('mediacenter_profile', 'mediacenter_profile_path')
        self.table.setCellWidget(row_num, constants.EditorCols.MEDIACENTER_PROFILE.value, self._create_merged_path_widget(game.get('mediacenter_profile_enabled', True), mediacenter_profile, game.get('mediacenter_profile_overwrite', True), row_num, constants.EditorCols.MEDIACENTER_PROFILE.value))

        # Just After Launch (CheckBox, Path with symbol, RunWait)
        ja_symbol, ja_run_wait = self._get_propagation_symbol_and_run_wait('just_after_launch_path')
        ja_path = f"{ja_symbol} {game.get('just_after_launch_path', '').lstrip('<> ')}"
        self.table.setCellWidget(row_num, constants.EditorCols.JA_PATH.value, self._create_merged_path_widget(game.get('just_after_launch_enabled', True), ja_path, game.get('just_after_launch_overwrite', True), row_num, constants.EditorCols.JA_PATH.value))
        self.table.setCellWidget(row_num, constants.EditorCols.JA_RUN_WAIT.value, self._create_checkbox_widget(game.get('just_after_launch_run_wait', ja_run_wait), row_num, constants.EditorCols.JA_RUN_WAIT.value))

        # Just Before Exit (CheckBox, Path with symbol, RunWait)
        jb_symbol, jb_run_wait = self._get_propagation_symbol_and_run_wait('just_before_exit_path')
        jb_path = f"{jb_symbol} {game.get('just_before_exit_path', '').lstrip('<> ')}"
        self.table.setCellWidget(row_num, constants.EditorCols.JB_PATH.value, self._create_merged_path_widget(game.get('just_before_exit_enabled', True), jb_path, game.get('just_before_exit_overwrite', True), row_num, constants.EditorCols.JB_PATH.value))
        self.table.setCellWidget(row_num, constants.EditorCols.JB_RUN_WAIT.value, self._create_checkbox_widget(game.get('just_before_exit_run_wait', jb_run_wait), row_num, constants.EditorCols.JB_RUN_WAIT.value))

        # Pre/Post Scripts with Enabled Checkboxes and RunWait toggles
        pre1_symbol, pre1_run_wait = self._get_propagation_symbol_and_run_wait('pre1_path')
        pre1_path = f"{pre1_symbol} {game.get('pre1_path', '').lstrip('<> ')}"
        self.table.setCellWidget(row_num, constants.EditorCols.PRE1_PATH.value, self._create_merged_path_widget(game.get('pre_1_enabled', True), pre1_path, game.get('pre_1_overwrite', True), row_num, constants.EditorCols.PRE1_PATH.value))
        self.table.setCellWidget(row_num, constants.EditorCols.PRE1_RUN_WAIT.value, self._create_checkbox_widget(game.get('pre_1_run_wait', pre1_run_wait), row_num, constants.EditorCols.PRE1_RUN_WAIT.value))

        post1_symbol, post1_run_wait = self._get_propagation_symbol_and_run_wait('post1_path')
        post1_path = f"{post1_symbol} {game.get('post1_path', '').lstrip('<> ')}"
        self.table.setCellWidget(row_num, constants.EditorCols.POST1_PATH.value, self._create_merged_path_widget(game.get('post_1_enabled', True), post1_path, game.get('post_1_overwrite', True), row_num, constants.EditorCols.POST1_PATH.value))
        self.table.setCellWidget(row_num, constants.EditorCols.POST1_RUN_WAIT.value, self._create_checkbox_widget(game.get('post_1_run_wait', post1_run_wait), row_num, constants.EditorCols.POST1_RUN_WAIT.value))

        pre2_symbol, pre2_run_wait = self._get_propagation_symbol_and_run_wait('pre2_path')
        pre2_path = f"{pre2_symbol} {game.get('pre2_path', '').lstrip('<> ')}"
        self.table.setCellWidget(row_num, constants.EditorCols.PRE2_PATH.value, self._create_merged_path_widget(game.get('pre_2_enabled', True), pre2_path, game.get('pre_2_overwrite', True), row_num, constants.EditorCols.PRE2_PATH.value))
        self.table.setCellWidget(row_num, constants.EditorCols.PRE2_RUN_WAIT.value, self._create_checkbox_widget(game.get('pre_2_run_wait', pre2_run_wait), row_num, constants.EditorCols.PRE2_RUN_WAIT.value))

        post2_symbol, post2_run_wait = self._get_propagation_symbol_and_run_wait('post2_path')
        post2_path = f"{post2_symbol} {game.get('post2_path', '').lstrip('<> ')}"
        self.table.setCellWidget(row_num, constants.EditorCols.POST2_PATH.value, self._create_merged_path_widget(game.get('post_2_enabled', True), post2_path, game.get('post_2_overwrite', True), row_num, constants.EditorCols.POST2_PATH.value))
        self.table.setCellWidget(row_num, constants.EditorCols.POST2_RUN_WAIT.value, self._create_checkbox_widget(game.get('post_2_run_wait', post2_run_wait), row_num, constants.EditorCols.POST2_RUN_WAIT.value))

        pre3_symbol, pre3_run_wait = self._get_propagation_symbol_and_run_wait('pre3_path')
        pre3_path = f"{pre3_symbol} {game.get('pre3_path', '').lstrip('<> ')}"
        self.table.setCellWidget(row_num, constants.EditorCols.PRE3_PATH.value, self._create_merged_path_widget(game.get('pre_3_enabled', True), pre3_path, game.get('pre_3_overwrite', True), row_num, constants.EditorCols.PRE3_PATH.value))
        self.table.setCellWidget(row_num, constants.EditorCols.PRE3_RUN_WAIT.value, self._create_checkbox_widget(game.get('pre_3_run_wait', pre3_run_wait), row_num, constants.EditorCols.PRE3_RUN_WAIT.value))

        post3_symbol, post3_run_wait = self._get_propagation_symbol_and_run_wait('post3_path')
        post3_path = f"{post3_symbol} {game.get('post3_path', '').lstrip('<> ')}"
        self.table.setCellWidget(row_num, constants.EditorCols.POST3_PATH.value, self._create_merged_path_widget(game.get('post_3_enabled', True), post3_path, game.get('post_3_overwrite', True), row_num, constants.EditorCols.POST3_PATH.value))
        self.table.setCellWidget(row_num, constants.EditorCols.POST3_RUN_WAIT.value, self._create_checkbox_widget(game.get('post_3_run_wait', post3_run_wait), row_num, constants.EditorCols.POST3_RUN_WAIT.value))

        # Kill List (Merged: CheckBox + Text)
        kl_item = QTableWidgetItem(game.get('kill_list', ''))
        kl_enabled = game.get('kill_list_enabled', False)
        kl_item.setCheckState(Qt.CheckState.Checked if kl_enabled else Qt.CheckState.Unchecked)
        self.table.setItem(row_num, constants.EditorCols.KILL_LIST.value, kl_item)

        self.table.blockSignals(False) # Unblock signals

    def get_all_game_data(self):
        """Extract all game data from the table."""
        return self.original_data

    def get_selected_game_data(self):
        """Extract data for selected games in the table."""
        selected_games = []
        for item in self.table.selectedItems():
            if item.column() == constants.EditorCols.NAME.value: # NAME column (column 1) contains the executable name
                row = item.row()
                real_index = (self.current_page * self.page_size) + row
                if real_index < len(self.filtered_data):
                    game_data = self.filtered_data[real_index]
                    selected_games.append(game_data)
        return selected_games

    def get_create_count(self):
        """Return the number of items marked for creation in the full dataset."""
        return sum(1 for g in self.original_data if g.get('create', False))

    def apply_cell_value_to_selection(self, src_row, col):
        state = self._get_cell_state(src_row, col)
        if state is None:
            return

        rows = set()
        # Get rows from selected ranges
        for range_ in self.table.selectedRanges():
            for r in range(range_.topRow(), range_.bottomRow() + 1):
                rows.add(r)
        
        # Fallback to selected indexes if ranges are empty
        if not rows:
            for index in self.table.selectedIndexes():
                rows.add(index.row())
        
        # Apply to all unique rows
        for r in rows:
            if r == src_row: continue
            self._set_cell_state(r, col, state)
            self._sync_cell_to_data(r, col)
            
        # Notify change
        self.main_window._on_editor_table_edited(None)

    def _get_cell_state(self, row, col):
        widget = self.table.cellWidget(row, col)
        if widget:
            cbs = widget.findChildren(QCheckBox)
            if len(cbs) >= 2: # Merged
                enabled = cbs[0].isChecked()
                overwrite = cbs[1].isChecked()
                le = widget.findChild(QLineEdit)
                path = le.text() if le else ""
                return {'type': 'merged', 'enabled': enabled, 'path': path, 'overwrite': overwrite}
            elif len(cbs) == 1: # Simple Checkbox
                return {'type': 'checkbox', 'checked': cbs[0].isChecked()}
        
        item = self.table.item(row, col)
        if item:
            state = {'type': 'text', 'text': item.text()}
            # Handle merged Kill List (checkable text)
            if col == constants.EditorCols.KILL_LIST.value:
                state['checked'] = (item.checkState() == Qt.CheckState.Checked)
                state['type'] = 'checkable_text'
            return state
        return None

    def _set_cell_state(self, row, col, state):
        if not state: return
        
        if state['type'] == 'merged':
            widget = self.table.cellWidget(row, col)
            if widget:
                cbs = widget.findChildren(QCheckBox)
                if len(cbs) >= 2:
                    cbs[0].setChecked(state['enabled'])
                    cbs[1].setChecked(state['overwrite'])
                    le = widget.findChild(QLineEdit)
                    if le: le.setText(state['path'])
        
        elif state['type'] == 'checkbox':
            widget = self.table.cellWidget(row, col)
            if widget:
                cbs = widget.findChildren(QCheckBox)
                if cbs:
                    cbs[0].setChecked(state['checked'])
                    
        elif state['type'] == 'checkable_text':
            item = self.table.item(row, col)
            if not item:
                item = QTableWidgetItem()
                self.table.setItem(row, col, item)
            item.setText(state['text'])
            item.setCheckState(Qt.CheckState.Checked if state.get('checked', False) else Qt.CheckState.Unchecked)

        elif state['type'] == 'text':
            item = self.table.item(row, col)
            if not item:
                item = QTableWidgetItem()
                self.table.setItem(row, col, item)
            item.setText(state['text'])

    def clear_table(self):
        """Clear the table and reset original data."""
        self.table.setRowCount(0)
        self.original_data = []
        self.filtered_data = []
        self.current_page = 0
        self.data_changed.emit()