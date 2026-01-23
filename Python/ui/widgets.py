from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QFileDialog, QAbstractItemView
)
from PyQt6.QtCore import pyqtSignal, Qt
from qfluentwidgets import (
    ListWidget, LineEdit, CheckBox, ToolButton, PushButton, FluentIcon as FIF, RoundMenu
)

class DragDropListWidget(ListWidget):
    """A ListWidget that supports drag and drop reordering using Fluent UI."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

class PathConfigRow(QWidget):
    """A row widget for configuring a path with optional features using Fluent UI."""
    valueChanged = pyqtSignal()
    downloadRequested = pyqtSignal(str, dict) # tool_name, tool_data

    def __init__(self, config_key, is_directory=False, add_enabled=False, 
                 add_run_wait=False, add_cen_lc=False, repo_items=None, parent=None):
        super().__init__(parent)
        self.config_key = config_key
        self.is_directory = is_directory
        self.repo_items = repo_items or {}
        self._mode = "CEN" # Default mode

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Enabled Checkbox
        self.enabled_cb = CheckBox(self)
        self.enabled_cb.setText("")
        self.enabled_cb.setVisible(add_enabled)
        self.enabled_cb.stateChanged.connect(self.valueChanged.emit)
        layout.addWidget(self.enabled_cb)

        # Path LineEdit
        self.line_edit = LineEdit(self)
        self.line_edit.setPlaceholderText("Select path..." if is_directory else "Select executable...")
        self.line_edit.textChanged.connect(self.valueChanged.emit)
        layout.addWidget(self.line_edit)

        # Browse Button
        self.browse_btn = ToolButton(FIF.FOLDER, self)
        self.browse_btn.setToolTip("Browse")
        self.browse_btn.clicked.connect(self._browse)
        layout.addWidget(self.browse_btn)

        # Download Button (if repo items exist)
        if self.repo_items:
            self.download_btn = ToolButton(FIF.DOWNLOAD, self)
            self.download_btn.setToolTip("Download Tool")
            self.download_btn.clicked.connect(self._show_download_menu)
            layout.addWidget(self.download_btn)

        # Run/Wait Checkbox
        self.run_wait_cb = CheckBox("Wait", self)
        self.run_wait_cb.setToolTip("Wait for this application to close before continuing")
        self.run_wait_cb.setVisible(add_run_wait)
        self.run_wait_cb.stateChanged.connect(self.valueChanged.emit)
        layout.addWidget(self.run_wait_cb)

        # Mode Toggle (CEN/LC)
        if add_cen_lc:
            self.mode_btn = PushButton("CEN", self)
            self.mode_btn.setFixedWidth(50)
            self.mode_btn.setToolTip("Deployment Mode: Centralized (CEN) or Local Copy (LC)")
            self.mode_btn.clicked.connect(self._toggle_mode)
            layout.addWidget(self.mode_btn)
        else:
            self.mode_btn = None

    def _browse(self):
        if self.is_directory:
            path = QFileDialog.getExistingDirectory(self, "Select Directory", self.line_edit.text())
        else:
            path, _ = QFileDialog.getOpenFileName(self, "Select File", self.line_edit.text())
        
        if path:
            self.line_edit.setText(path)

    def _toggle_mode(self):
        self._mode = "LC" if self._mode == "CEN" else "CEN"
        self.mode_btn.setText(self._mode)
        self.valueChanged.emit()

    def _show_download_menu(self):
        menu = RoundMenu(parent=self)
        for name, data in self.repo_items.items():
            action = menu.addAction(name)
            action.triggered.connect(lambda checked, n=name, d=data: self.downloadRequested.emit(n, d))
        
        menu.exec(self.download_btn.mapToGlobal(self.download_btn.rect().bottomLeft()))

    @property
    def path(self): return self.line_edit.text()
    @path.setter
    def path(self, v): self.line_edit.setText(v)

    @property
    def enabled(self): return self.enabled_cb.isChecked()
    @enabled.setter
    def enabled(self, v): self.enabled_cb.setChecked(v)

    @property
    def run_wait(self): return self.run_wait_cb.isChecked()
    @run_wait.setter
    def run_wait(self, v): self.run_wait_cb.setChecked(v)

    @property
    def mode(self): return self._mode
    @mode.setter
    def mode(self, v):
        self._mode = v
        if self.mode_btn: self.mode_btn.setText(v)