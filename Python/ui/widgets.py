from PyQt6.QtWidgets import (QListWidget, QAbstractItemView, QWidget, QHBoxLayout,
                             QCheckBox, QLineEdit, QPushButton, QRadioButton, QComboBox,
                             QButtonGroup, QFileDialog, QToolButton, QMenu, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal
import os

class DragDropListWidget(QListWidget):
    """A list widget that supports drag and drop for reordering items"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setDropIndicatorShown(True)
    
    def dropEvent(self, event):
        """Handle drop events for reordering"""
        super().dropEvent(event)
        
        # Emit a signal to notify that the order has changed
        self.model().layoutChanged.emit()

class PathConfigRow(QWidget):
    """Custom widget for a path configuration row with options."""
    valueChanged = pyqtSignal()
    downloadRequested = pyqtSignal(str, dict)  # tool_name, tool_data

    def __init__(self, config_key, is_directory=False, add_enabled=True,
                 add_run_wait=False, add_cen_lc=True, repo_items=None, use_combobox=True, parent=None):
        super().__init__(parent)
        self.config_key = config_key
        self.is_directory = is_directory
        self.add_enabled = add_enabled
        self.add_run_wait = add_run_wait
        self._overwrite = True
        self.use_combobox = use_combobox
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Enabled Checkbox
        if self.add_enabled:
            self.enabled_cb = QCheckBox()
            self.enabled_cb.setChecked(True)
            self.enabled_cb.setToolTip("Enable/Disable this application")
            self.enabled_cb.stateChanged.connect(self.valueChanged.emit)
            layout.addWidget(self.enabled_cb)
        else:
            self.enabled_cb = None

        if self.use_combobox:
            # ComboBox
            self.combo = QComboBox()
            self.combo.setEditable(True)
            self.combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
            self.combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            self.combo.lineEdit().editingFinished.connect(self._on_editing_finished)
            self.combo.lineEdit().textChanged.connect(self._check_styling)
            self.combo.currentIndexChanged.connect(self.valueChanged.emit)
            layout.addWidget(self.combo)
            self.line_edit = None
        else:
            # Line Edit
            self.line_edit = QLineEdit()
            self.line_edit.editingFinished.connect(self.valueChanged.emit)
            self.line_edit.textChanged.connect(self._check_styling)
            layout.addWidget(self.line_edit)
            self.combo = None

        # Repo Flyout Button
        self.tool_btn = None
        if repo_items:
            self.tool_btn = QToolButton()
            self.tool_btn.setText("▼")
            self.tool_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
            self.tool_btn.setToolTip("Download/Select Tool")
            self.menu = QMenu()
            
            for name, data in repo_items.items():
                action = self.menu.addAction(name)
                # Use default arguments to capture loop variables correctly
                action.triggered.connect(lambda _, n=name, d=data: self.downloadRequested.emit(n, d))
            
            self.tool_btn.setMenu(self.menu)
            layout.addWidget(self.tool_btn)

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
            self.mode_group.buttonClicked.connect(self._check_styling)
            layout.addWidget(self.cen_radio)
            layout.addWidget(self.lc_radio)
        else:
            self.cen_radio = self.lc_radio = self.mode_group = None

        # Populate from repo_items if available
        if repo_items and self.use_combobox:
            for name, data in repo_items.items():
                if 'extract_dir' in data and 'exe_name' in data:
                    exe_path = os.path.join(data['extract_dir'], data['exe_name'])
                    if os.path.exists(exe_path):
                        if self.combo.findText(exe_path) == -1:
                            self.combo.addItem(exe_path)

        # Run Wait Checkbox
        if self.add_run_wait:
            self.run_wait_cb = QCheckBox("Wait")
            self.run_wait_cb.stateChanged.connect(self.valueChanged.emit)
            layout.addWidget(self.run_wait_cb)
        else:
            self.run_wait_cb = None
            
        # Initial check
        self._check_styling()
        
        # Connect enabled checkbox to UI update
        if self.enabled_cb:
            self.enabled_cb.stateChanged.connect(self._update_ui_state)
            self._update_ui_state()

    def _on_editing_finished(self):
        """Handle editing finished to manage history."""
        text = self.combo.currentText().strip()
        if text:
            # If path exists and not in list, add it
            if os.path.exists(text):
                if self.combo.findText(text) == -1:
                    self.combo.addItem(text)
        else:
            # If text is empty, remove the current item if it exists
            idx = self.combo.currentIndex()
            if idx >= 0:
                self.combo.removeItem(idx)
        self.valueChanged.emit()

    def _check_styling(self):
        """Apply styling if LC is enabled and file > 10MB."""
        # Styling removed - no visual indicators for LC/CEN modes
        pass

    def _update_ui_state(self):
        """Enable or disable widgets based on the enabled checkbox."""
        if not self.enabled_cb:
            return
            
        is_enabled = self.enabled_cb.isChecked()
        
        if self.use_combobox:
            self.combo.setEnabled(is_enabled)
        else:
            self.line_edit.setEnabled(is_enabled)
        self.browse_btn.setEnabled(is_enabled)
        
        if self.tool_btn:
            self.tool_btn.setEnabled(is_enabled)
            
        if self.cen_radio:
            self.cen_radio.setEnabled(is_enabled)
        if self.lc_radio:
            self.lc_radio.setEnabled(is_enabled)
            
        if self.run_wait_cb:
            self.run_wait_cb.setEnabled(is_enabled)

    def _on_browse(self):
        current_path = self.path
        if self.is_directory:
            directory = QFileDialog.getExistingDirectory(self, "Select Directory", current_path)
            if directory:
                self.path = directory
        else:
            file, _ = QFileDialog.getOpenFileName(self, "Select File", current_path)
            if file:
                self.path = file

    @property
    def path(self):
        if self.use_combobox:
            return self.combo.currentText()
        else:
            return self.line_edit.text()

    @path.setter
    def path(self, value):
        if self.use_combobox:
            self.combo.setCurrentText(value)
            self._on_editing_finished() # Ensure it's added to history if valid
        else:
            self.line_edit.setText(value)
            # For line edit, we might want to trigger styling check manually if needed
            self._check_styling()

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
        self._check_styling()

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

    @property
    def overwrite(self):
        return self._overwrite

    @overwrite.setter
    def overwrite(self, value):
        self._overwrite = value
        self._check_styling()