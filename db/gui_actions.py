from django.core.exceptions import FieldDoesNotExist
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QCheckBox,
    QTreeView, QStyledItemDelegate, QStyle, QComboBox, QDialog, QListView,
    QStyleOptionButton, QApplication,
)
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QDrag, QPainter, QPalette
from PyQt6.QtCore import Qt, QModelIndex, pyqtSignal, QMimeData, QThread, pyqtSlot, QObject


class CelebrateListWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Не забудьте поздравить')


class ActionsHumanWidget(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.main_window = main_window

        btn_show_holidays = QPushButton('Кого поздравлять?')
        btn_show_holidays.clicked.connect(self.on_click_show_holidays)
        layout.addWidget(btn_show_holidays)
    
    def on_click_show_holidays(self):
        window = CelebrateListWindow()
        window.exec()
