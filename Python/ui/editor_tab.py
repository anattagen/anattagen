from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QLabel,
    QPushButton, QHeaderView, QAbstractItemView, QMenu, QCheckBox, QLineEdit
)
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
        self.populate_ui()

    def populate_ui(self):
        """Create and arrange widgets for the editor tab."""
        main_layout = QVBoxLayout(self)

        # --- Table ---
        self.table = QTableWidget()
        # set column count based on EditorCols mapping
        self.table.setColumnCount(max(c.value for c in constants.EditorCols) + 1)
        self.table.setHorizontalHeaderLabels([
            "Create", "Name", "Directory", "SteamID",
            "NameOverride", "Options", "Arguments", "RunAsAdmin",
            "CM En", "Controller Mapper", "CM Rw",
            "BW En", "Borderless Windowing", "BW Rw",
            "MM En", "Multi-Monitor", "MM Rw",
            "Hide Taskbar",
            "MM Game Profile", "MM Desktop Profile",
            "Player 1 Profile", "Player 2 Profile", "MediaCenter Profile",
            "JA En", "Just After Launch", "JA Rw",
            "JB En", "Just Before Exit", "JB Rw",
            "Pre1En", "Pre1", "Pre1Rw",
            "Pst1En", "Post1", "Pst1Rw",
            "Pre2En", "Pre2", "Pre2Rw",
            "Pst2En", "Post2", "Pst2Rw",
            "Pre3En", "Pre3", "Pre3Rw",
            "Pst3En", "Post3", "Pst3Rw"
        ])
        # Shorten width for Enabled (En) and Run/Wait (Rw) columns to save space
        try:
            en_columns = [constants.EditorCols.CM_ENABLED.value, constants.EditorCols.BW_ENABLED.value,
                          constants.EditorCols.MM_ENABLED.value, constants.EditorCols.JA_ENABLED.value,
                          constants.EditorCols.JB_ENABLED.value, constants.EditorCols.PRE1_ENABLED.value,
                          constants.EditorCols.POST1_ENABLED.value, constants.EditorCols.PRE2_ENABLED.value,
                          constants.EditorCols.POST2_ENABLED.value, constants.EditorCols.PRE3_ENABLED.value,
                          constants.EditorCols.POST3_ENABLED.value]
            rw_columns = [constants.EditorCols.CM_RUN_WAIT.value, constants.EditorCols.BW_RUN_WAIT.value,
                          constants.EditorCols.MM_RUN_WAIT.value, constants.EditorCols.JA_RUN_WAIT.value,
                          constants.EditorCols.JB_RUN_WAIT.value, constants.EditorCols.PRE1_RUN_WAIT.value,
                          constants.EditorCols.POST1_RUN_WAIT.value, constants.EditorCols.PRE2_RUN_WAIT.value,
                          constants.EditorCols.POST2_RUN_WAIT.value, constants.EditorCols.PRE3_RUN_WAIT.value,
                          constants.EditorCols.POST3_RUN_WAIT.value]

            for col in en_columns + rw_columns:
                # Use a conservative small width; UI can still resize if needed
                self.table.setColumnWidth(col, 56)
        except Exception:
            pass
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.AllEditTriggers)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        main_layout.addWidget(self.table)

        # --- Buttons ---
        buttons_layout = QHBoxLayout()
        self.save_button = QPushButton("Save Index")
        self.load_button = QPushButton("Load Index")
        self.delete_button = QPushButton("Delete Indexes")
        self.clear_button = QPushButton("Clear View")
        self.regenerate_names_button = QPushButton("Regenerate All Names")
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.load_button)
        buttons_layout.addWidget(self.delete_button)
        buttons_layout.addWidget(self.clear_button)
        buttons_layout.addWidget(self.regenerate_names_button)
        main_layout.addLayout(buttons_layout)

        # --- Connect Signals ---
        self.save_button.clicked.connect(self.save_index_requested.emit)
        self.load_button.clicked.connect(self.load_index_requested.emit)
        self.delete_button.clicked.connect(self.delete_indexes_requested.emit)
        self.clear_button.clicked.connect(self.clear_view_requested.emit)
        self.regenerate_names_button.clicked.connect(self.main_window._regenerate_all_names)

        self.table.customContextMenuRequested.connect(self.on_context_menu)
        self.table.cellClicked.connect(self.on_cell_clicked)
        self.table.itemChanged.connect(self.on_item_changed)

    def on_context_menu(self, position):
        """Create and display custom context menu for the table."""
        self.main_window._on_editor_table_custom_context_menu(position)

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

    def populate_from_data(self, data):
        """Populate the table with data."""
        if not data:
            print("populate_from_data: No data received, returning.")
            return

        print(f"populate_from_data: Received {len(data)} items to populate.")
        self.table.setRowCount(0)
        for row_num, game in enumerate(data):
            self.table.insertRow(row_num)
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
            print(f"  [EditorTab:populate] Row {row_num} ('{game.get('name')}'): Populating with steam_id: '{steam_id_value}'")
            self.table.setItem(row_num, constants.EditorCols.STEAMID.value, QTableWidgetItem(str(steam_id_value)))

            # NameOverride - col NAME_OVERRIDE
            self.table.setItem(row_num, constants.EditorCols.NAME_OVERRIDE.value, QTableWidgetItem(game.get('name_override', '')))

            # Options - col OPTIONS
            self.table.setItem(row_num, constants.EditorCols.OPTIONS.value, QTableWidgetItem(game.get('options', '')))

            # Arguments - col ARGUMENTS
            self.table.setItem(row_num, constants.EditorCols.ARGUMENTS.value, QTableWidgetItem(game.get('arguments', '')))

            # RunAsAdmin (CheckBox) - col RUN_AS_ADMIN
            self.table.setCellWidget(row_num, constants.EditorCols.RUN_AS_ADMIN.value, self._create_checkbox_widget(game.get('run_as_admin', False)))

            # Helper to get propagation status symbol and run_wait default
            def _get_propagation_symbol_and_run_wait(config_key):
                """Get propagation status symbol (< or >) and default run_wait state from config"""
                config = self.main_window.config
                # Get the propagation mode (CEN or LC)
                mode = config.deployment_path_modes.get(config_key, 'CEN')
                symbol = '<' if mode == 'CEN' else '>'
                
                # Get the run_wait default state
                run_wait_key = f"{config_key}_run_wait"
                run_wait = config.run_wait_states.get(run_wait_key, False)
                
                return symbol, run_wait

            # Controller Mapper (CheckBox, Path with symbol, RunWait)
            # Merged widget for Path column
            cm_symbol, cm_run_wait = _get_propagation_symbol_and_run_wait('controller_mapper_path')
            cm_path = f"{cm_symbol} {game.get('controller_mapper_path', '')}"
            self.table.setCellWidget(row_num, constants.EditorCols.CM_PATH.value, self._create_merged_path_widget(game.get('controller_mapper_enabled', True), cm_path, game.get('controller_mapper_overwrite', True)))
            self.table.setCellWidget(row_num, constants.EditorCols.CM_RUN_WAIT.value, self._create_checkbox_widget(game.get('controller_mapper_run_wait', cm_run_wait)))

            # Borderless Windowing (CheckBox, Path with symbol, RunWait)
            bw_symbol, bw_run_wait = _get_propagation_symbol_and_run_wait('borderless_gaming_path')
            bw_path = f"{bw_symbol} {game.get('borderless_windowing_path', '')}"
            self.table.setCellWidget(row_num, constants.EditorCols.BW_PATH.value, self._create_merged_path_widget(game.get('borderless_windowing_enabled', True), bw_path, game.get('borderless_windowing_overwrite', True)))
            self.table.setCellWidget(row_num, constants.EditorCols.BW_RUN_WAIT.value, self._create_checkbox_widget(game.get('borderless_windowing_run_wait', bw_run_wait)))

            # Multi-monitor App (CheckBox, Path with symbol, RunWait)
            mm_symbol, mm_run_wait = _get_propagation_symbol_and_run_wait('multi_monitor_tool_path')
            mm_path = f"{mm_symbol} {game.get('multi_monitor_app_path', '')}"
            self.table.setCellWidget(row_num, constants.EditorCols.MM_PATH.value, self._create_merged_path_widget(game.get('multi_monitor_app_enabled', True), mm_path, game.get('multi_monitor_app_overwrite', True)))
            self.table.setCellWidget(row_num, constants.EditorCols.MM_RUN_WAIT.value, self._create_checkbox_widget(game.get('multi_monitor_app_run_wait', mm_run_wait)))

            # Hide Taskbar (CheckBox)
            self.table.setCellWidget(row_num, constants.EditorCols.HIDE_TASKBAR.value, self._create_checkbox_widget(game.get('hide_taskbar', False)))

            # Profiles with propagation symbols
            config = self.main_window.config
            mm_game_symbol, _ = _get_propagation_symbol_and_run_wait('multimonitor_gaming_path')
            mm_game_profile = f"{mm_game_symbol} {game.get('mm_game_profile', '')}"
            self.table.setItem(row_num, constants.EditorCols.MM_GAME_PROFILE.value, QTableWidgetItem(mm_game_profile))
            
            mm_desktop_symbol, _ = _get_propagation_symbol_and_run_wait('multimonitor_media_path')
            mm_desktop_profile = f"{mm_desktop_symbol} {game.get('mm_desktop_profile', '')}"
            self.table.setItem(row_num, constants.EditorCols.MM_DESKTOP_PROFILE.value, QTableWidgetItem(mm_desktop_profile))
            
            p1_symbol, _ = _get_propagation_symbol_and_run_wait('p1_profile_path')
            player1_profile = f"{p1_symbol} {game.get('player1_profile', '')}"
            self.table.setItem(row_num, constants.EditorCols.PLAYER1_PROFILE.value, QTableWidgetItem(player1_profile))
            
            p2_symbol, _ = _get_propagation_symbol_and_run_wait('p2_profile_path')
            player2_profile = f"{p2_symbol} {game.get('player2_profile', '')}"
            self.table.setItem(row_num, constants.EditorCols.PLAYER2_PROFILE.value, QTableWidgetItem(player2_profile))
            
            mc_symbol, _ = _get_propagation_symbol_and_run_wait('mediacenter_profile_path')
            mediacenter_profile = f"{mc_symbol} {game.get('mediacenter_profile', '')}"
            self.table.setItem(row_num, constants.EditorCols.MEDIACENTER_PROFILE.value, QTableWidgetItem(mediacenter_profile))

            # Just After Launch (CheckBox, Path with symbol, RunWait)
            ja_symbol, ja_run_wait = _get_propagation_symbol_and_run_wait('just_after_launch_path')
            ja_path = f"{ja_symbol} {game.get('just_after_launch_path', '')}"
            self.table.setCellWidget(row_num, constants.EditorCols.JA_PATH.value, self._create_merged_path_widget(game.get('just_after_launch_enabled', True), ja_path, game.get('just_after_launch_overwrite', True)))
            self.table.setCellWidget(row_num, constants.EditorCols.JA_RUN_WAIT.value, self._create_checkbox_widget(game.get('just_after_launch_run_wait', ja_run_wait)))

            # Just Before Exit (CheckBox, Path with symbol, RunWait)
            jb_symbol, jb_run_wait = _get_propagation_symbol_and_run_wait('just_before_exit_path')
            jb_path = f"{jb_symbol} {game.get('just_before_exit_path', '')}"
            self.table.setCellWidget(row_num, constants.EditorCols.JB_PATH.value, self._create_merged_path_widget(game.get('just_before_exit_enabled', True), jb_path, game.get('just_before_exit_overwrite', True)))
            self.table.setCellWidget(row_num, constants.EditorCols.JB_RUN_WAIT.value, self._create_checkbox_widget(game.get('just_before_exit_run_wait', jb_run_wait)))

            # Pre/Post Scripts with Enabled Checkboxes and RunWait toggles
            pre1_symbol, pre1_run_wait = _get_propagation_symbol_and_run_wait('pre1_path')
            pre1_path = f"{pre1_symbol} {game.get('pre1_path', '')}"
            self.table.setCellWidget(row_num, constants.EditorCols.PRE1_PATH.value, self._create_merged_path_widget(game.get('pre_1_enabled', True), pre1_path, game.get('pre_1_overwrite', True)))
            self.table.setCellWidget(row_num, constants.EditorCols.PRE1_RUN_WAIT.value, self._create_checkbox_widget(game.get('pre_1_run_wait', pre1_run_wait)))

            post1_symbol, post1_run_wait = _get_propagation_symbol_and_run_wait('post1_path')
            post1_path = f"{post1_symbol} {game.get('post1_path', '')}"
            self.table.setCellWidget(row_num, constants.EditorCols.POST1_PATH.value, self._create_merged_path_widget(game.get('post_1_enabled', True), post1_path, game.get('post_1_overwrite', True)))
            self.table.setCellWidget(row_num, constants.EditorCols.POST1_RUN_WAIT.value, self._create_checkbox_widget(game.get('post_1_run_wait', post1_run_wait)))

            pre2_symbol, pre2_run_wait = _get_propagation_symbol_and_run_wait('pre2_path')
            pre2_path = f"{pre2_symbol} {game.get('pre2_path', '')}"
            self.table.setCellWidget(row_num, constants.EditorCols.PRE2_PATH.value, self._create_merged_path_widget(game.get('pre_2_enabled', True), pre2_path, game.get('pre_2_overwrite', True)))
            self.table.setCellWidget(row_num, constants.EditorCols.PRE2_RUN_WAIT.value, self._create_checkbox_widget(game.get('pre_2_run_wait', pre2_run_wait)))

            post2_symbol, post2_run_wait = _get_propagation_symbol_and_run_wait('post2_path')
            post2_path = f"{post2_symbol} {game.get('post2_path', '')}"
            self.table.setCellWidget(row_num, constants.EditorCols.POST2_PATH.value, self._create_merged_path_widget(game.get('post_2_enabled', True), post2_path, game.get('post_2_overwrite', True)))
            self.table.setCellWidget(row_num, constants.EditorCols.POST2_RUN_WAIT.value, self._create_checkbox_widget(game.get('post_2_run_wait', post2_run_wait)))

            pre3_symbol, pre3_run_wait = _get_propagation_symbol_and_run_wait('pre3_path')
            pre3_path = f"{pre3_symbol} {game.get('pre3_path', '')}"
            self.table.setCellWidget(row_num, constants.EditorCols.PRE3_PATH.value, self._create_merged_path_widget(game.get('pre_3_enabled', True), pre3_path, game.get('pre_3_overwrite', True)))
            self.table.setCellWidget(row_num, constants.EditorCols.PRE3_RUN_WAIT.value, self._create_checkbox_widget(game.get('pre_3_run_wait', pre3_run_wait)))

            post3_symbol, post3_run_wait = _get_propagation_symbol_and_run_wait('post3_path')
            post3_path = f"{post3_symbol} {game.get('post3_path', '')}"
            self.table.setCellWidget(row_num, constants.EditorCols.POST3_PATH.value, self._create_merged_path_widget(game.get('post_3_enabled', True), post3_path, game.get('post_3_overwrite', True)))
            self.table.setCellWidget(row_num, constants.EditorCols.POST3_RUN_WAIT.value, self._create_checkbox_widget(game.get('post_3_run_wait', post3_run_wait)))

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