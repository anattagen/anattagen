from PyQt6.QtCore import Qt
from qfluentwidgets import MessageBoxBase, SubtitleLabel, LineEdit, BodyLabel

class FluentInputDialog(MessageBoxBase):
    """A Fluent UI replacement for QInputDialog.getText"""
    def __init__(self, title, label, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel(title, self)
        self.textLabel = BodyLabel(label, self)
        self.lineEdit = LineEdit(self)
        
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.textLabel)
        self.viewLayout.addWidget(self.lineEdit)
        
        self.yesButton.setText("OK")
        self.cancelButton.setText("Cancel")
        
        self.widget.setMinimumWidth(350)
        self.lineEdit.setFocus()

    def setText(self, text):
        self.lineEdit.setText(text)
        self.lineEdit.selectAll()

    def textValue(self):
        return self.lineEdit.text()