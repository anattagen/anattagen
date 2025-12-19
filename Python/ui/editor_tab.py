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
        self.table.setColumnCount(23)
        self.table.setHorizontalHeaderLabels([
            "Create", "Name", "Directory", "SteamID", 
            "NameOverride", "Options", "Arguments", "RunAsAdmin",
            "Borderless-Windowing", "Hide Taskbar", "MM Game Profile", "MM Desktop Profile",
            "Player 1 Profile", "Player 2 Profile", "MediaCenterProfile",
            "JustBeforeLaunch", "JustAfterExit",
            "Pre1", "Post1", "Pre2", "Post2", "Pre3", "Post3"
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

            # Borderless-Windowing (CheckBox) - col 8
            self.table.setCellWidget(row_num, 8, self._create_checkbox_widget(game.get('borderless_windowing', False)))

            # Hide Taskbar (CheckBox) - col 9
            self.table.setCellWidget(row_num, 9, self._create_checkbox_widget(game.get('hide_taskbar', False)))

            # MM Game Profile - col 10
            self.table.setItem(row_num, 10, QTableWidgetItem(game.get('mm_game_profile', '')))

            # MM Desktop Profile - col 11
            self.table.setItem(row_num, 11, QTableWidgetItem(game.get('mm_desktop_profile', '')))

            # Player 1 Profile - col 12
            self.table.setItem(row_num, 12, QTableWidgetItem(game.get('player1_profile', '')))

            # Player 2 Profile - col 13
            self.table.setItem(row_num, 13, QTableWidgetItem(game.get('player2_profile', '')))

            # MediaCenterProfile - col 14
            self.table.setItem(row_num, 14, QTableWidgetItem(game.get('mediacenter_profile', '')))

            # JustBeforeLaunch - col 15
            self.table.setItem(row_num, 15, QTableWidgetItem(game.get('just_before_launch', '')))

            # JustAfterExit - col 16
            self.table.setItem(row_num, 16, QTableWidgetItem(game.get('just_after_exit', '')))

            # Pre1 - col 17
            self.table.setItem(row_num, 17, QTableWidgetItem(game.get('pre1', '')))

            # Post1 - col 18
            self.table.setItem(row_num, 18, QTableWidgetItem(game.get('post1', '')))

            # Pre2 - col 19
            self.table.setItem(row_num, 19, QTableWidgetItem(game.get('pre2', '')))

            # Post2 - col 20
            self.table.setItem(row_num, 20, QTableWidgetItem(game.get('post2', '')))

            # Pre3 - col 21
            self.table.setItem(row_num, 21, QTableWidgetItem(game.get('pre3', '')))

            # Post3 - col 22
            self.table.setItem(row_num, 22, QTableWidgetItem(game.get('post3', '')))

    def get_all_game_data(self):
        """Extract all game data from the table."""
        data = []
        for row in range(self.table.rowCount()):
            game = {}

            # Override (CheckBox)
            override_widget = self.table.cellWidget(row, 0)
            if override_widget:
                override_layout = override_widget.layout()
                if override_layout:
                    override_checkbox = override_layout.itemAt(0).widget()
                    game['override'] = override_checkbox.isChecked()

            # Executable (Text)
            game['exec_name'] = self.table.item(row, 1).text() if self.table.item(row, 1) else ''

            # Directory (Text)
            game['directory'] = self.table.item(row, 2).text() if self.table.item(row, 2) else ''

            # AppID (Text)
            game['steam_appid'] = self.table.item(row, 3).text() if self.table.item(row, 3) else ''

            # Name (Text)
            game['name_override'] = self.table.item(row, 4).text() if self.table.item(row, 4) else ''

            # Arguments (Text)
            game['arguments'] = self.table.item(row, 5).text() if self.table.item(row, 5) else ''

            # Run (Text)
            game['run'] = self.table.item(row, 6).text() if self.table.item(row, 6) else ''

            # Monitor (Text)
            game['monitor'] = self.table.item(row, 7).text() if self.table.item(row, 7) else ''

            # Audio (Text)
            game['audio'] = self.table.item(row, 8).text() if self.table.item(row, 8) else ''

            # Profile (Text)
            game['joystick_profile'] = self.table.item(row, 9).text() if self.table.item(row, 9) else ''

            # Notes (Text)
            game['notes'] = self.table.item(row, 10).text() if self.table.item(row, 10) else ''

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