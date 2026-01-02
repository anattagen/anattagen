from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QLabel,
    QPushButton, QHeaderView, QAbstractItemView, QMenu, QCheckBox, QLineEdit,
    QApplication, QFileDialog, QInputDialog, QMessageBox
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

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.table = None
        self.original_data = []
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

        # Shorten width for Enabled (En) and Run/Wait (Rw) columns to save space
        try:
            rw_columns = [constants.EditorCols.CM_RUN_WAIT.value, constants.EditorCols.BW_RUN_WAIT.value,
                          constants.EditorCols.MM_RUN_WAIT.value, constants.EditorCols.JA_RUN_WAIT.value,
                          constants.EditorCols.JB_RUN_WAIT.value, constants.EditorCols.PRE1_RUN_WAIT.value,
                          constants.EditorCols.POST1_RUN_WAIT.value, constants.EditorCols.PRE2_RUN_WAIT.value,
                          constants.EditorCols.POST2_RUN_WAIT.value, constants.EditorCols.PRE3_RUN_WAIT.value,
                          constants.EditorCols.POST3_RUN_WAIT.value]

            for col in rw_columns:
                # Use a conservative small width; UI can still resize if needed
                self.table.setColumnWidth(col, 30)
            
            self.table.setColumnWidth(constants.EditorCols.WIN_EXIT.value, 56)
            self.table.setColumnWidth(constants.EditorCols.RUN_AS_ADMIN.value, 60)

            # Reduce width of opts, args, and Directory by 80%
            shrink_cols = [constants.EditorCols.DIRECTORY.value, constants.EditorCols.OPTIONS.value, constants.EditorCols.ARGUMENTS.value]
            for col in shrink_cols:
                self.table.setColumnWidth(col, 40)
        except Exception:
            pass
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(False)
        header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        header.customContextMenuRequested.connect(self.on_header_context_menu)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.AllEditTriggers)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        main_layout.addWidget(self.table)

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

    def filter_table(self, text):
        """Filter table rows based on game name."""
        text = text.lower()
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, constants.EditorCols.NAME.value)
            name_override_item = self.table.item(row, constants.EditorCols.NAME_OVERRIDE.value)
            
            name = name_item.text().lower() if name_item else ""
            name_override = name_override_item.text().lower() if name_override_item else ""
            
            if text in name or text in name_override:
                self.table.setRowHidden(row, False)
            else:
                self.table.setRowHidden(row, True)

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
        
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.original_data.append(copy.deepcopy(game_data))
        self._populate_row(row, game_data)
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
        
        # Edit
        edit_action = menu.addAction("Edit this Field")
        edit_action.triggered.connect(lambda: self.edit_cell(row, col))
        
        # Select Row
        select_row_action = menu.addAction("Select Row")
        select_row_action.triggered.connect(lambda: self.table.selectRow(row))
        
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
        self.main_window._on_editor_table_edited(item)

    def _create_checkbox_widget(self, checked: bool) -> QWidget:
        """Create a centered checkbox widget for table cells."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        checkbox = QCheckBox()
        checkbox.setChecked(checked)
        layout.addWidget(checkbox)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        return widget

    def _create_merged_path_widget(self, enabled: bool, path_text: str, overwrite: bool) -> QWidget:
        """Create a merged widget with Enabled checkbox, Path label, and Overwrite checkbox."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setSpacing(6)
        
        cb_enabled = QCheckBox()
        cb_enabled.setChecked(enabled)
        cb_enabled.setToolTip("Enable")
        
        label = QLabel(path_text)
        label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        cb_overwrite = QCheckBox()
        cb_overwrite.setChecked(overwrite)
        cb_overwrite.setToolTip("Overwrite")
        
        layout.addWidget(cb_enabled)
        layout.addWidget(label, 1)
        layout.addWidget(cb_overwrite)
        
        return widget

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
            lbl = widget.findChild(QLabel)
            path = lbl.text() if lbl else ""
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
            print("populate_from_data: No data received, returning.")
            return

        print(f"populate_from_data: Received {len(data)} items to populate.")
        self.original_data = [copy.deepcopy(game) for game in data]
        self.table.setRowCount(0)
        for row_num, game in enumerate(data):
            self.table.insertRow(row_num)
            self._populate_row(row_num, game)

    def _populate_row(self, row_num, game):
        """Populate a single row with game data."""
        self.table.blockSignals(True) # Block signals during population

        # Create (CheckBox) - col INCLUDE
        self.table.setCellWidget(row_num, constants.EditorCols.INCLUDE.value, self._create_checkbox_widget(game.get('create', False)))

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
        self.table.setCellWidget(row_num, constants.EditorCols.RUN_AS_ADMIN.value, self._create_checkbox_widget(game.get('run_as_admin', False)))

        # Controller Mapper (CheckBox, Path with symbol, RunWait)
        # Merged widget for Path column
        cm_symbol, cm_run_wait = self._get_propagation_symbol_and_run_wait('controller_mapper_path')
        cm_path = f"{cm_symbol} {game.get('controller_mapper_path', '').lstrip('<> ')}"
        self.table.setCellWidget(row_num, constants.EditorCols.CM_PATH.value, self._create_merged_path_widget(game.get('controller_mapper_enabled', True), cm_path, game.get('controller_mapper_overwrite', True)))
        self.table.setCellWidget(row_num, constants.EditorCols.CM_RUN_WAIT.value, self._create_checkbox_widget(game.get('controller_mapper_run_wait', cm_run_wait)))

        # Borderless Windowing (CheckBox, Path with symbol, RunWait)
        bw_symbol, bw_run_wait = self._get_propagation_symbol_and_run_wait('borderless_gaming_path')
        bw_path = f"{bw_symbol} {game.get('borderless_windowing_path', '').lstrip('<> ')}"
        self.table.setCellWidget(row_num, constants.EditorCols.BW_PATH.value, self._create_merged_path_widget(game.get('borderless_windowing_enabled', True), bw_path, game.get('borderless_windowing_overwrite', True)))
        self.table.setCellWidget(row_num, constants.EditorCols.BW_RUN_WAIT.value, self._create_checkbox_widget(game.get('borderless_windowing_run_wait', bw_run_wait)))
        
        # Win-Exit
        self.table.setCellWidget(row_num, constants.EditorCols.WIN_EXIT.value, self._create_checkbox_widget(game.get('terminate_borderless_on_exit', self.main_window.config.terminate_borderless_on_exit)))

        # Multi-monitor App (CheckBox, Path with symbol, RunWait)
        mm_symbol, mm_run_wait = self._get_propagation_symbol_and_run_wait('multi_monitor_tool_path')
        mm_path = f"{mm_symbol} {game.get('multi_monitor_app_path', '').lstrip('<> ')}"
        self.table.setCellWidget(row_num, constants.EditorCols.MM_PATH.value, self._create_merged_path_widget(game.get('multi_monitor_app_enabled', True), mm_path, game.get('multi_monitor_app_overwrite', True)))
        self.table.setCellWidget(row_num, constants.EditorCols.MM_RUN_WAIT.value, self._create_checkbox_widget(game.get('multi_monitor_app_run_wait', mm_run_wait)))

        # Hide Taskbar (CheckBox)
        self.table.setCellWidget(row_num, constants.EditorCols.HIDE_TASKBAR.value, self._create_checkbox_widget(game.get('hide_taskbar', False)))

        # Profiles with propagation symbols
        mm_game_symbol, _ = self._get_propagation_symbol_and_run_wait('multimonitor_gaming_path')
        mm_game_profile = f"{mm_game_symbol} {game.get('mm_game_profile', '').lstrip('<> ')}"
        self.table.setItem(row_num, constants.EditorCols.MM_GAME_PROFILE.value, QTableWidgetItem(mm_game_profile))
        
        mm_desktop_symbol, _ = self._get_propagation_symbol_and_run_wait('multimonitor_media_path')
        mm_desktop_profile = f"{mm_desktop_symbol} {game.get('mm_desktop_profile', '').lstrip('<> ')}"
        self.table.setItem(row_num, constants.EditorCols.MM_DESKTOP_PROFILE.value, QTableWidgetItem(mm_desktop_profile))
        
        p1_symbol, _ = self._get_propagation_symbol_and_run_wait('p1_profile_path')
        player1_profile = f"{p1_symbol} {game.get('player1_profile', '').lstrip('<> ')}"
        self.table.setItem(row_num, constants.EditorCols.PLAYER1_PROFILE.value, QTableWidgetItem(player1_profile))
        
        p2_symbol, _ = self._get_propagation_symbol_and_run_wait('p2_profile_path')
        player2_profile = f"{p2_symbol} {game.get('player2_profile', '').lstrip('<> ')}"
        self.table.setItem(row_num, constants.EditorCols.PLAYER2_PROFILE.value, QTableWidgetItem(player2_profile))
        
        mc_symbol, _ = self._get_propagation_symbol_and_run_wait('mediacenter_profile_path')
        mediacenter_profile = f"{mc_symbol} {game.get('mediacenter_profile', '').lstrip('<> ')}"
        self.table.setItem(row_num, constants.EditorCols.MEDIACENTER_PROFILE.value, QTableWidgetItem(mediacenter_profile))

        # Just After Launch (CheckBox, Path with symbol, RunWait)
        ja_symbol, ja_run_wait = self._get_propagation_symbol_and_run_wait('just_after_launch_path')
        ja_path = f"{ja_symbol} {game.get('just_after_launch_path', '').lstrip('<> ')}"
        self.table.setCellWidget(row_num, constants.EditorCols.JA_PATH.value, self._create_merged_path_widget(game.get('just_after_launch_enabled', True), ja_path, game.get('just_after_launch_overwrite', True)))
        self.table.setCellWidget(row_num, constants.EditorCols.JA_RUN_WAIT.value, self._create_checkbox_widget(game.get('just_after_launch_run_wait', ja_run_wait)))

        # Just Before Exit (CheckBox, Path with symbol, RunWait)
        jb_symbol, jb_run_wait = self._get_propagation_symbol_and_run_wait('just_before_exit_path')
        jb_path = f"{jb_symbol} {game.get('just_before_exit_path', '').lstrip('<> ')}"
        self.table.setCellWidget(row_num, constants.EditorCols.JB_PATH.value, self._create_merged_path_widget(game.get('just_before_exit_enabled', True), jb_path, game.get('just_before_exit_overwrite', True)))
        self.table.setCellWidget(row_num, constants.EditorCols.JB_RUN_WAIT.value, self._create_checkbox_widget(game.get('just_before_exit_run_wait', jb_run_wait)))

        # Pre/Post Scripts with Enabled Checkboxes and RunWait toggles
        pre1_symbol, pre1_run_wait = self._get_propagation_symbol_and_run_wait('pre1_path')
        pre1_path = f"{pre1_symbol} {game.get('pre1_path', '').lstrip('<> ')}"
        self.table.setCellWidget(row_num, constants.EditorCols.PRE1_PATH.value, self._create_merged_path_widget(game.get('pre_1_enabled', True), pre1_path, game.get('pre_1_overwrite', True)))
        self.table.setCellWidget(row_num, constants.EditorCols.PRE1_RUN_WAIT.value, self._create_checkbox_widget(game.get('pre_1_run_wait', pre1_run_wait)))

        post1_symbol, post1_run_wait = self._get_propagation_symbol_and_run_wait('post1_path')
        post1_path = f"{post1_symbol} {game.get('post1_path', '').lstrip('<> ')}"
        self.table.setCellWidget(row_num, constants.EditorCols.POST1_PATH.value, self._create_merged_path_widget(game.get('post_1_enabled', True), post1_path, game.get('post_1_overwrite', True)))
        self.table.setCellWidget(row_num, constants.EditorCols.POST1_RUN_WAIT.value, self._create_checkbox_widget(game.get('post_1_run_wait', post1_run_wait)))

        pre2_symbol, pre2_run_wait = self._get_propagation_symbol_and_run_wait('pre2_path')
        pre2_path = f"{pre2_symbol} {game.get('pre2_path', '').lstrip('<> ')}"
        self.table.setCellWidget(row_num, constants.EditorCols.PRE2_PATH.value, self._create_merged_path_widget(game.get('pre_2_enabled', True), pre2_path, game.get('pre_2_overwrite', True)))
        self.table.setCellWidget(row_num, constants.EditorCols.PRE2_RUN_WAIT.value, self._create_checkbox_widget(game.get('pre_2_run_wait', pre2_run_wait)))

        post2_symbol, post2_run_wait = self._get_propagation_symbol_and_run_wait('post2_path')
        post2_path = f"{post2_symbol} {game.get('post2_path', '').lstrip('<> ')}"
        self.table.setCellWidget(row_num, constants.EditorCols.POST2_PATH.value, self._create_merged_path_widget(game.get('post_2_enabled', True), post2_path, game.get('post_2_overwrite', True)))
        self.table.setCellWidget(row_num, constants.EditorCols.POST2_RUN_WAIT.value, self._create_checkbox_widget(game.get('post_2_run_wait', post2_run_wait)))

        pre3_symbol, pre3_run_wait = self._get_propagation_symbol_and_run_wait('pre3_path')
        pre3_path = f"{pre3_symbol} {game.get('pre3_path', '').lstrip('<> ')}"
        self.table.setCellWidget(row_num, constants.EditorCols.PRE3_PATH.value, self._create_merged_path_widget(game.get('pre_3_enabled', True), pre3_path, game.get('pre_3_overwrite', True)))
        self.table.setCellWidget(row_num, constants.EditorCols.PRE3_RUN_WAIT.value, self._create_checkbox_widget(game.get('pre_3_run_wait', pre3_run_wait)))

        post3_symbol, post3_run_wait = self._get_propagation_symbol_and_run_wait('post3_path')
        post3_path = f"{post3_symbol} {game.get('post3_path', '').lstrip('<> ')}"
        self.table.setCellWidget(row_num, constants.EditorCols.POST3_PATH.value, self._create_merged_path_widget(game.get('post_3_enabled', True), post3_path, game.get('post_3_overwrite', True)))
        self.table.setCellWidget(row_num, constants.EditorCols.POST3_RUN_WAIT.value, self._create_checkbox_widget(game.get('post_3_run_wait', post3_run_wait)))

        # Kill List (Merged: CheckBox + Text)
        kl_item = QTableWidgetItem(game.get('kill_list', ''))
        kl_enabled = game.get('kill_list_enabled', False)
        kl_item.setCheckState(Qt.CheckState.Checked if kl_enabled else Qt.CheckState.Unchecked)
        self.table.setItem(row_num, constants.EditorCols.KILL_LIST.value, kl_item)

        self.table.blockSignals(False) # Unblock signals

    def get_all_game_data(self):
        """Extract all game data from the table."""
        data = []
        for row in range(self.table.rowCount()):
            game = {}

            # Column 0: Create (CheckBox)
            game['create'] = self._get_checkbox_value(row, constants.EditorCols.INCLUDE.value)

            # Column 1: Name (Text)
            game['name'] = self.table.item(row, constants.EditorCols.NAME.value).text() if self.table.item(row, constants.EditorCols.NAME.value) else ''

            # Column 2: Directory (Text)
            game['directory'] = self.table.item(row, constants.EditorCols.DIRECTORY.value).text() if self.table.item(row, constants.EditorCols.DIRECTORY.value) else ''

            # Column 3: SteamID (Text)
            steam_id_item = self.table.item(row, constants.EditorCols.STEAMID.value)
            steam_id_text = steam_id_item.text() if steam_id_item else 'ITEM_IS_NONE'
            game['steam_id'] = steam_id_text
            game_name_for_log = self.table.item(row, constants.EditorCols.NAME.value).text() if self.table.item(row, constants.EditorCols.NAME.value) else 'UNKNOWN_GAME'
            print(f"  [EditorTab:get_data] Row {row} ('{game_name_for_log}'): Reading steam_id from table: '{steam_id_text}'")

            # Column 4: NameOverride (Text)
            game['name_override'] = self.table.item(row, constants.EditorCols.NAME_OVERRIDE.value).text() if self.table.item(row, constants.EditorCols.NAME_OVERRIDE.value) else ''

            # Column 5: Options (Text)
            game['options'] = self.table.item(row, constants.EditorCols.OPTIONS.value).text() if self.table.item(row, constants.EditorCols.OPTIONS.value) else ''

            # Column 6: Arguments (Text)
            game['arguments'] = self.table.item(row, constants.EditorCols.ARGUMENTS.value).text() if self.table.item(row, constants.EditorCols.ARGUMENTS.value) else ''

            # Column 7: RunAsAdmin (CheckBox)
            game['run_as_admin'] = self._get_checkbox_value(row, constants.EditorCols.RUN_AS_ADMIN.value)

            # Controller Mapper (cols 8-10)
            cm_enabled, cm_path_full, cm_overwrite = self._get_merged_path_data(row, constants.EditorCols.CM_PATH.value)
            game['controller_mapper_enabled'] = cm_enabled
            game['controller_mapper_path'] = cm_path_full.lstrip('<> ') # Strip symbol
            game['controller_mapper_overwrite'] = cm_overwrite
            game['controller_mapper_run_wait'] = self._get_checkbox_value(row, constants.EditorCols.CM_RUN_WAIT.value)

            # Borderless Windowing (cols 11-13)
            bw_enabled, bw_path_full, bw_overwrite = self._get_merged_path_data(row, constants.EditorCols.BW_PATH.value)
            game['borderless_windowing_enabled'] = bw_enabled
            game['borderless_windowing_path'] = bw_path_full.lstrip('<> ')
            game['borderless_windowing_overwrite'] = bw_overwrite
            game['borderless_windowing_run_wait'] = self._get_checkbox_value(row, constants.EditorCols.BW_RUN_WAIT.value)
            
            # Win-Exit (col 12)
            game['terminate_borderless_on_exit'] = self._get_checkbox_value(row, constants.EditorCols.WIN_EXIT.value)

            # Multi-monitor App (cols 14-16)
            mm_enabled, mm_path_full, mm_overwrite = self._get_merged_path_data(row, constants.EditorCols.MM_PATH.value)
            game['multi_monitor_app_enabled'] = mm_enabled
            game['multi_monitor_app_path'] = mm_path_full.lstrip('<> ')
            game['multi_monitor_app_overwrite'] = mm_overwrite
            game['multi_monitor_app_run_wait'] = self._get_checkbox_value(row, constants.EditorCols.MM_RUN_WAIT.value)

            # Hide Taskbar (col 17)
            game['hide_taskbar'] = self._get_checkbox_value(row, constants.EditorCols.HIDE_TASKBAR.value)

            # Profiles (cols 18-22)
            game['mm_game_profile'] = self.table.item(row, constants.EditorCols.MM_GAME_PROFILE.value).text() if self.table.item(row, constants.EditorCols.MM_GAME_PROFILE.value) else ''
            game['mm_desktop_profile'] = self.table.item(row, constants.EditorCols.MM_DESKTOP_PROFILE.value).text() if self.table.item(row, constants.EditorCols.MM_DESKTOP_PROFILE.value) else ''
            game['player1_profile'] = self.table.item(row, constants.EditorCols.PLAYER1_PROFILE.value).text() if self.table.item(row, constants.EditorCols.PLAYER1_PROFILE.value) else ''
            game['player2_profile'] = self.table.item(row, constants.EditorCols.PLAYER2_PROFILE.value).text() if self.table.item(row, constants.EditorCols.PLAYER2_PROFILE.value) else ''
            game['mediacenter_profile'] = self.table.item(row, constants.EditorCols.MEDIACENTER_PROFILE.value).text() if self.table.item(row, constants.EditorCols.MEDIACENTER_PROFILE.value) else ''

            # Just After Launch (cols 23-25)
            ja_enabled, ja_path_full, ja_overwrite = self._get_merged_path_data(row, constants.EditorCols.JA_PATH.value)
            game['just_after_launch_enabled'] = ja_enabled
            game['just_after_launch_path'] = ja_path_full.lstrip('<> ')
            game['just_after_launch_overwrite'] = ja_overwrite
            game['just_after_launch_run_wait'] = self._get_checkbox_value(row, constants.EditorCols.JA_RUN_WAIT.value)

            # Just Before Exit (cols 26-28)
            jb_enabled, jb_path_full, jb_overwrite = self._get_merged_path_data(row, constants.EditorCols.JB_PATH.value)
            game['just_before_exit_enabled'] = jb_enabled
            game['just_before_exit_path'] = jb_path_full.lstrip('<> ')
            game['just_before_exit_overwrite'] = jb_overwrite
            game['just_before_exit_run_wait'] = self._get_checkbox_value(row, constants.EditorCols.JB_RUN_WAIT.value)

            # Pre/Post scripts (cols 29-46)
            pre1_enabled, pre1_path_full, pre1_overwrite = self._get_merged_path_data(row, constants.EditorCols.PRE1_PATH.value)
            game['pre_1_enabled'] = pre1_enabled
            game['pre1_path'] = pre1_path_full.lstrip('<> ')
            game['pre_1_overwrite'] = pre1_overwrite
            game['pre_1_run_wait'] = self._get_checkbox_value(row, constants.EditorCols.PRE1_RUN_WAIT.value)

            post1_enabled, post1_path_full, post1_overwrite = self._get_merged_path_data(row, constants.EditorCols.POST1_PATH.value)
            game['post_1_enabled'] = post1_enabled
            game['post1_path'] = post1_path_full.lstrip('<> ')
            game['post_1_overwrite'] = post1_overwrite
            game['post_1_run_wait'] = self._get_checkbox_value(row, constants.EditorCols.POST1_RUN_WAIT.value)

            pre2_enabled, pre2_path_full, pre2_overwrite = self._get_merged_path_data(row, constants.EditorCols.PRE2_PATH.value)
            game['pre_2_enabled'] = pre2_enabled
            game['pre2_path'] = pre2_path_full.lstrip('<> ')
            game['pre_2_overwrite'] = pre2_overwrite
            game['pre_2_run_wait'] = self._get_checkbox_value(row, constants.EditorCols.PRE2_RUN_WAIT.value)

            post2_enabled, post2_path_full, post2_overwrite = self._get_merged_path_data(row, constants.EditorCols.POST2_PATH.value)
            game['post_2_enabled'] = post2_enabled
            game['post2_path'] = post2_path_full.lstrip('<> ')
            game['post_2_overwrite'] = post2_overwrite
            game['post_2_run_wait'] = self._get_checkbox_value(row, constants.EditorCols.POST2_RUN_WAIT.value)

            pre3_enabled, pre3_path_full, pre3_overwrite = self._get_merged_path_data(row, constants.EditorCols.PRE3_PATH.value)
            game['pre_3_enabled'] = pre3_enabled
            game['pre3_path'] = pre3_path_full.lstrip('<> ')
            game['pre_3_overwrite'] = pre3_overwrite
            game['pre_3_run_wait'] = self._get_checkbox_value(row, constants.EditorCols.PRE3_RUN_WAIT.value)

            post3_enabled, post3_path_full, post3_overwrite = self._get_merged_path_data(row, constants.EditorCols.POST3_PATH.value)
            game['post_3_enabled'] = post3_enabled
            game['post3_path'] = post3_path_full.lstrip('<> ')
            game['post_3_overwrite'] = post3_overwrite
            game['post_3_run_wait'] = self._get_checkbox_value(row, constants.EditorCols.POST3_RUN_WAIT.value)

            # Kill List (Merged)
            kl_item = self.table.item(row, constants.EditorCols.KILL_LIST.value)
            if kl_item:
                game['kill_list_enabled'] = (kl_item.checkState() == Qt.CheckState.Checked)
                game['kill_list'] = kl_item.text()
            else:
                game['kill_list_enabled'] = False
                game['kill_list'] = ''

            data.append(game)
        return data

    def get_selected_game_data(self):
        """Extract data for selected games in the table."""
        selected_games = []
        for item in self.table.selectedItems():
            if item.column() == constants.EditorCols.NAME.value: # NAME column (column 1) contains the executable name
                row = item.row()
                game_data = self.get_all_game_data()[row]
                selected_games.append(game_data)
        return selected_games

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
            
        # Notify change
        self.main_window._on_editor_table_edited(None)

    def _get_cell_state(self, row, col):
        widget = self.table.cellWidget(row, col)
        if widget:
            cbs = widget.findChildren(QCheckBox)
            if len(cbs) >= 2: # Merged
                enabled = cbs[0].isChecked()
                overwrite = cbs[1].isChecked()
                lbl = widget.findChild(QLabel)
                path = lbl.text() if lbl else ""
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
                    lbl = widget.findChild(QLabel)
                    if lbl: lbl.setText(state['path'])
        
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