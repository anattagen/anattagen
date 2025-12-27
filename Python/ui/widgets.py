from PyQt6.QtWidgets import (QListWidget, QAbstractItemView, QWidget, QHBoxLayout,
                             QCheckBox, QLineEdit, QPushButton, QRadioButton,
                             QButtonGroup, QFileDialog)
from PyQt6.QtCore import Qt, QMimeData, pyqtSignal
from PyQt6.QtGui import QDrag

class DragDropListWidget(QListWidget):
    """A list widget that supports drag and drop for reordering items"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    
    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.pos()
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events for drag and drop"""
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        
        if not hasattr(self, 'drag_start_position'):
            return
        
        if (event.pos() - self.drag_start_position).manhattanLength() < 10:
            return
        
        drag = QDrag(self)
        mime_data = QMimeData()
        
        # Store the row index in the mime data
        current_item = self.currentItem()
        if current_item:
            mime_data.setText(str(self.row(current_item)))
            drag.setMimeData(mime_data)
            
            # Start the drag operation
            drag.exec(Qt.DropAction.MoveAction)
    
    def dropEvent(self, event):
        """Handle drop events for reordering"""
        super().dropEvent(event)
        
        # Emit a signal to notify that the order has changed
        self.model().layoutChanged.emit()

class PathConfigRow(QWidget):
    """Custom widget for a path configuration row with options."""
    valueChanged = pyqtSignal()

    def __init__(self, config_key, is_directory=False, add_enabled=True,
                 add_run_wait=False, add_cen_lc=True, parent=None):
        super().__init__(parent)
        self.config_key = config_key
        self.is_directory = is_directory
        self.add_enabled = add_enabled
        self.add_run_wait = add_run_wait
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Enabled Checkbox
        if self.add_enabled:
            self.enabled_cb = QCheckBox()
            self.enabled_cb.setChecked(True)
            self.enabled_cb.stateChanged.connect(self.valueChanged.emit)
            layout.addWidget(self.enabled_cb)
        else:
            self.enabled_cb = None

        # Line Edit
        self.line_edit = QLineEdit()
        self.line_edit.textChanged.connect(self.valueChanged.emit)
        layout.addWidget(self.line_edit)

        # Browse Button
        self.browse_btn = QPushButton(". . .")
        self.browse_btn.setFixedWidth(40)
        self.browse_btn.clicked.connect(self._on_browse)
        layout.addWidget(self.browse_btn)

        # CEN/LC Radio Buttons
        if add_cen_lc:
            self.cen_radio = QRadioButton("CEN")
            self.lc_radio = QRadioButton("LC")
            self.cen_radio.setChecked(True)
            self.mode_group = QButtonGroup(self)
            self.mode_group.addButton(self.cen_radio)
            self.mode_group.addButton(self.lc_radio)
            self.mode_group.buttonClicked.connect(self.valueChanged.emit)
            layout.addWidget(self.cen_radio)
            layout.addWidget(self.lc_radio)
        else:
            self.cen_radio = self.lc_radio = self.mode_group = None

        # Run Wait Checkbox
        if self.add_run_wait:
            self.run_wait_cb = QCheckBox("Wait")
            self.run_wait_cb.stateChanged.connect(self.valueChanged.emit)
            layout.addWidget(self.run_wait_cb)
        else:
            self.run_wait_cb = None

    def _on_browse(self):
        current_path = self.line_edit.text()
        if self.is_directory:
            directory = QFileDialog.getExistingDirectory(self, "Select Directory", current_path)
            if directory:
                self.line_edit.setText(directory)
        else:
            file, _ = QFileDialog.getOpenFileName(self, "Select File", current_path)
            if file:
                self.line_edit.setText(file)

    @property
    def path(self):
        return self.line_edit.text()

    @path.setter
    def path(self, value):
        self.line_edit.setText(value)

    @property
    def mode(self):
        if self.lc_radio and self.lc_radio.isChecked():
            return "LC"
        return "CEN"

    @mode.setter
    def mode(self, value):
        if self.mode_group:
            if value == "LC":
                self.lc_radio.setChecked(True)
            else:
                self.cen_radio.setChecked(True)

    @property
    def enabled(self):
        return self.enabled_cb.isChecked() if self.enabled_cb else True

    @enabled.setter
    def enabled(self, value):
        if self.enabled_cb:
            self.enabled_cb.setChecked(value)

    @property
    def run_wait(self):
        return self.run_wait_cb.isChecked() if self.run_wait_cb else False

    @run_wait.setter
    def run_wait(self, value):
        if self.run_wait_cb:
            self.run_wait_cb.setChecked(value)