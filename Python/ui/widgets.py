from PyQt6.QtWidgets import QListWidget, QAbstractItemView
from PyQt6.QtCore import Qt, QMimeData
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