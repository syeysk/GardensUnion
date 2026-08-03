import os
import sys

import django
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from django.conf import settings

from common.gui_main_window import MainWindow
from db.gui_windows import GUIHuman, GUICommunity, GUITask, GUIContact, GUIMeeting


class MainWindow(MainWindow):
    def __init__(self):
        self.gui_models = [GUIHuman, GUICommunity, GUITask, GUIContact, GUIMeeting]
        super().__init__()
        self.setWindowTitle('HumanEnv - Your human environment')
        self.setWindowIcon(QIcon(str(settings.BASE_DIR.parent / 'images/tie_butterfly.jpg')))
        self.entity_types.select_current()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
