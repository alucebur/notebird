"""User-defined widgets."""
from PySide2 import QtWidgets, QtCore


class ClickableLineEdit(QtWidgets.QLineEdit):
    """LineEdit widget that sends a signal when clicked on it."""

    clicked = QtCore.Signal()

    def __init__(self, parent):
        super().__init__(parent)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.clicked.emit()


class ClickablePlainTextEdit(QtWidgets.QPlainTextEdit):
    """PlainTextEdit widget that sends a signal when clicked on it."""

    clicked = QtCore.Signal()

    def __init__(self, parent):
        super().__init__(parent)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.clicked.emit()
