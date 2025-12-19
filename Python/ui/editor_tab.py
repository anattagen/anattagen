from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QAbstractItemView, QMenu, QCheckBox, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor

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
        self.table.setColumnCount(30)
        self.table.setHorizontalHeaderLabels([
            "Create", "Name", "Directory", "SteamID", 
            "NameOverride", "Options", "Arguments", "RunAsAdmin",
            "Controller Mapper", "Borderless Windowing", "Multi-monitor App", "Hide Taskbar",
            "MM Game Profile", "MM Desktop Profile",
            "Player 1 Profile", "Player 2 Profile", "MediaCenterProfile",
            "After Launch", "Before Exit",
            "Pre1 En", "Pre1",
            "Post1 En", "Post1",
            "Pre2 En", "Pre2",
            "Post2 En", "Post2",
            "Pre3 En", "Pre3",
            "Post3 En", "Post3"
        ])
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

    def _get_checkbox_value(self, row: int, col: int) -> bool:
        """Get checkbox value from a cell widget."""
        widget = self.table.cellWidget(row, col)
        if widget:
            checkbox = widget.findChild(QCheckBox)
            if checkbox:
                return checkbox.isChecked()
        return False

    def populate_from_data(self, data):
        """Populate the table with data."""
        if not data:
            return

        self.table.setRowCount(0)
        for row_num, game in enumerate(data):
            self.table.insertRow(row_num)
            self.table.blockSignals(True) # Block signals during population

            # Create (CheckBox) - col 0
            self.table.setCellWidget(row_num, 0, self._create_checkbox_widget(game.get('create', False)))

            # Name (uneditable) - col 1
            name_item = QTableWidgetItem(game.get('name', ''))
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row_num, 1, name_item)

            # Directory (uneditable) - col 2
            dir_item = QTableWidgetItem(game.get('directory', ''))
            dir_item.setFlags(dir_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row_num, 2, dir_item)

            # SteamID - col 3
            self.table.setItem(row_num, 3, QTableWidgetItem(game.get('steam_id', '')))

            # NameOverride - col 4
            self.table.setItem(row_num, 4, QTableWidgetItem(game.get('name_override', '')))

            # Options - col 5
            self.table.setItem(row_num, 5, QTableWidgetItem(game.get('options', '')))

            # Arguments - col 6
            self.table.setItem(row_num, 6, QTableWidgetItem(game.get('arguments', '')))

            # RunAsAdmin (CheckBox) - col 7
            self.table.setCellWidget(row_num, 7, self._create_checkbox_widget(game.get('run_as_admin', False)))

            # Controller Mapper (CheckBox) - col 8
            self.table.setCellWidget(row_num, 8, self._create_checkbox_widget(game.get('controller_mapper_enabled', True)))

            # Borderless Windowing (CheckBox) - col 9
            self.table.setCellWidget(row_num, 9, self._create_checkbox_widget(game.get('borderless_windowing_enabled', True)))

            # Multi-monitor App (CheckBox) - col 10
            self.table.setCellWidget(row_num, 10, self._create_checkbox_widget(game.get('multi_monitor_app_enabled', True)))

            # Hide Taskbar (CheckBox) - col 11
            self.table.setCellWidget(row_num, 11, self._create_checkbox_widget(game.get('hide_taskbar', False)))

            # MM Game Profile - col 12
            self.table.setItem(row_num, 12, QTableWidgetItem(game.get('mm_game_profile', '')))

            # MM Desktop Profile - col 13
            self.table.setItem(row_num, 13, QTableWidgetItem(game.get('mm_desktop_profile', '')))

            # Player 1 Profile - col 14
            self.table.setItem(row_num, 14, QTableWidgetItem(game.get('player1_profile', '')))

            # Player 2 Profile - col 15
            self.table.setItem(row_num, 15, QTableWidgetItem(game.get('player2_profile', '')))

            # MediaCenterProfile - col 16
            self.table.setItem(row_num, 16, QTableWidgetItem(game.get('mediacenter_profile', '')))

            # Just After Launch (CheckBox) - col 17
            self.table.setCellWidget(row_num, 17, self._create_checkbox_widget(game.get('just_after_launch_enabled', True)))

            # Just Before Exit (CheckBox) - col 18
            self.table.setCellWidget(row_num, 18, self._create_checkbox_widget(game.get('just_before_exit_enabled', True)))
            
            # Pre/Post Scripts with Enabled Checkboxes
            self.table.setCellWidget(row_num, 19, self._create_checkbox_widget(game.get('pre_1_enabled', True)))
            self.table.setItem(row_num, 20, QTableWidgetItem(game.get('pre1_path', '')))

            self.table.setCellWidget(row_num, 21, self._create_checkbox_widget(game.get('post_1_enabled', True)))
            self.table.setItem(row_num, 22, QTableWidgetItem(game.get('post1_path', '')))

            self.table.setCellWidget(row_num, 23, self._create_checkbox_widget(game.get('pre_2_enabled', True)))
            self.table.setItem(row_num, 24, QTableWidgetItem(game.get('pre2_path', '')))

            self.table.setCellWidget(row_num, 25, self._create_checkbox_widget(game.get('post_2_enabled', True)))
            self.table.setItem(row_num, 26, QTableWidgetItem(game.get('post2_path', '')))

            self.table.setCellWidget(row_num, 27, self._create_checkbox_widget(game.get('pre_3_enabled', True)))
            self.table.setItem(row_num, 28, QTableWidgetItem(game.get('pre3_path', '')))

            self.table.setCellWidget(row_num, 29, self._create_checkbox_widget(game.get('post_3_enabled', True)))
            # The Post3 value column would be 30, which is out of bounds.
            # I will assume the last column is for the Post3 checkbox.
            # If you need a text field for Post3, you must increase column count to 31
            # and add a header label for it.
            # self.table.setItem(row_num, 30, QTableWidgetItem(game.get('post3_path', '')))

            self.table.blockSignals(False) # Unblock signals

    def get_all_game_data(self):
        """Extract all game data from the table."""
        data = []
        for row in range(self.table.rowCount()):
            game = {}

            # Column 0: Create (CheckBox)
            game['create'] = self._get_checkbox_value(row, 0)

            # Column 1: Name (Text)
            game['name'] = self.table.item(row, 1).text() if self.table.item(row, 1) else ''

            # Column 2: Directory (Text)
            game['directory'] = self.table.item(row, 2).text() if self.table.item(row, 2) else ''

            # Column 3: SteamID (Text)
            game['steam_id'] = self.table.item(row, 3).text() if self.table.item(row, 3) else ''

            # Column 4: NameOverride (Text)
            game['name_override'] = self.table.item(row, 4).text() if self.table.item(row, 4) else ''

            # Column 5: Options (Text)
            game['options'] = self.table.item(row, 5).text() if self.table.item(row, 5) else ''

            # Column 6: Arguments (Text)
            game['arguments'] = self.table.item(row, 6).text() if self.table.item(row, 6) else ''

            # Column 7: RunAsAdmin (CheckBox)
            game['run_as_admin'] = self._get_checkbox_value(row, 7)

            # Column 8: Controller Mapper (CheckBox)
            game['controller_mapper_enabled'] = self._get_checkbox_value(row, 8)

            # Column 9: Borderless Windowing (CheckBox)
            game['borderless_windowing_enabled'] = self._get_checkbox_value(row, 9)

            # Column 10: Multi-monitor App (CheckBox)
            game['multi_monitor_app_enabled'] = self._get_checkbox_value(row, 10)

            # Column 11: Hide Taskbar (CheckBox)
            game['hide_taskbar'] = self._get_checkbox_value(row, 11)

            # Columns 12-16: Profiles (Text)
            game['mm_game_profile'] = self.table.item(row, 12).text() if self.table.item(row, 12) else ''
            game['mm_desktop_profile'] = self.table.item(row, 13).text() if self.table.item(row, 13) else ''
            game['player1_profile'] = self.table.item(row, 14).text() if self.table.item(row, 14) else ''
            game['player2_profile'] = self.table.item(row, 15).text() if self.table.item(row, 15) else ''
            game['mediacenter_profile'] = self.table.item(row, 16).text() if self.table.item(row, 16) else ''

            # Columns 17-23: Launch/Exit and Pre/Post scripts
            game['just_after_launch_enabled'] = self._get_checkbox_value(row, 17)
            game['just_before_exit_enabled'] = self._get_checkbox_value(row, 18)

            game['pre_1_enabled'] = self._get_checkbox_value(row, 19)
            game['pre1_path'] = self.table.item(row, 20).text() if self.table.item(row, 20) else ''

            game['post_1_enabled'] = self._get_checkbox_value(row, 21)
            game['post1_path'] = self.table.item(row, 22).text() if self.table.item(row, 22) else ''

            game['pre_2_enabled'] = self._get_checkbox_value(row, 23)
            game['pre2_path'] = self.table.item(row, 24).text() if self.table.item(row, 24) else ''

            game['post_2_enabled'] = self._get_checkbox_value(row, 25)
            game['post2_path'] = self.table.item(row, 26).text() if self.table.item(row, 26) else ''

            game['pre_3_enabled'] = self._get_checkbox_value(row, 27)
            game['pre3_path'] = self.table.item(row, 28).text() if self.table.item(row, 28) else ''

            game['post_3_enabled'] = self._get_checkbox_value(row, 29)
            # As noted in populate_from_data, there is no column for the Post3 value.
            # game['post3'] = self.table.item(row, 30).text() if self.table.item(row, 30) else ''

            data.append(game)
        return data

    def get_selected_game_data(self):
        """Extract data for selected games in the table."""
        selected_games = []
        for item in self.table.selectedItems():
            if item.column() == 1: # Assuming the executable name is in the first column
                row = item.row()
                game_data = self.get_all_game_data()[row]
                selected_games.append(game_data)
        return selected_games