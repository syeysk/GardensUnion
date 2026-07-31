import os
import sys

import django
from PyQt6.QtWidgets import QApplication, QVBoxLayout, QHBoxLayout
from PyQt6.QtGui import QIcon


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from django.conf import settings

from common.gui_entities_list import EntitiesList
from common.gui_entity import GUIEntity, EntityWindow
from common.gui_main_window import MainWindow
from db.gui_actions import ActionsHumanWidget
from db.models import (
    Community,
    Contact,
    Human,
    Task,
    Meeting,
    LinkContactHuman,
    LinkContactCommunity,
    LinkTaskHuman,
    LinkTaskCommunity,
    LinkTaskMeeting,
    LinkHumanMeeting,
    LinkHumanCommunity,
    LinkHumanHuman,

    ContactType,
    HumanRelationType,
    Sector,
    TaskAim,
)


class GUIHuman(GUIEntity):
    dj_model = Human
    table_class = EntitiesList
    window_class = EntityWindow
    table_fields = ['family_name', 'first_name']
    links = (
        ((LinkContactHuman, 'contact'), {}),
        ((LinkHumanCommunity, 'community'), {}),
        ((LinkHumanMeeting, 'meeting'), {}),
        ((LinkTaskHuman, 'task'), {}),
        ((LinkHumanHuman, 'human_linked'), {'fields': ['relation']}),
    )
    actions_class = ActionsHumanWidget
    field_order = 'family_name'
    fields_search = ['family_name', 'first_name', 'father_name']

    def build_form(self):
        layout_left = QVBoxLayout()
        field_names = ['sex', 'birth_year', 'birth_month', 'birth_day']
        for field_name in field_names:
            layout_line = self.build_row(field_name)
            layout_left.addLayout(layout_line)

        layout_right = QVBoxLayout()
        field_names = ['family_name', 'first_name', 'father_name', 'closing', 'circle', 'sector', 'book_contact_type', 'book_did']
        for field_name in field_names:
            layout_line = self.build_row(field_name)
            layout_right.addLayout(layout_line)

        layout_fields = QHBoxLayout()
        layout_fields.addLayout(layout_left)
        layout_fields.addLayout(layout_right)

        layout = QVBoxLayout()
        layout.addLayout(layout_fields)
        layout.addLayout(self.build_row('notes'))
        return layout


class GUICommunity(GUIEntity):
    dj_model = Community
    table_class = EntitiesList
    window_class = EntityWindow
    table_fields = ['name']
    links = (
        ((LinkHumanCommunity, 'human'), {}),
        ((LinkTaskCommunity, 'task'), {}),
    )

    def build_form(self):
        layout = QVBoxLayout()
        field_names = ['name']
        for field_name in field_names:
            layout_line = self.build_row(field_name)
            layout.addLayout(layout_line)

        return layout


class GUITask(GUIEntity):
    dj_model = Task
    table_class = EntitiesList
    window_class = EntityWindow
    table_fields = ['has_done', 'title']
    links = (
        ((LinkTaskHuman, 'human'), {}),
        ((LinkTaskCommunity, 'community'), {}),
        ((LinkTaskMeeting, 'meeting'), {}),
    )

    def build_form(self):
        layout = QVBoxLayout()
        field_names = ['title', 'aim', 'has_done']
        for field_name in field_names:
            layout_line = self.build_row(field_name)
            layout.addLayout(layout_line)

        return layout


class GUIContact(GUIEntity):
    dj_model = Contact
    table_class = EntitiesList
    window_class = EntityWindow
    table_fields = ['type', 'value', 'status']
    links = (
        ((LinkContactHuman, 'human'), {}),
        ((LinkContactCommunity, 'community'), {}),
    )

    def build_form(self):
        layout = QVBoxLayout()
        field_names = ['value', 'type', 'status']
        for field_name in field_names:
            layout_line = self.build_row(field_name)
            layout.addLayout(layout_line)

        return layout


class GUIMeeting(GUIEntity):
    dj_model = Meeting
    table_class = EntitiesList
    window_class = EntityWindow
    table_fields = ['title']
    links = (
        ((LinkHumanMeeting, 'human'), {}),
        ((LinkTaskMeeting, 'task'), {}),
    )

    def build_form(self):
        layout = QVBoxLayout()
        field_names = ['title', 'description', 'date']
        for field_name in field_names:
            layout_line = self.build_row(field_name)
            layout.addLayout(layout_line)

        return layout


# class GUIDynamicOptions(GUIEntity):
#     dj_model = None
#     table_fields = ['name']

#     def build_form(self):
#         layout = QVBoxLayout()
#         layout_line = self.build_row('name')
#         layout.addLayout(layout_line)
#         return layout


class GUISector(GUIEntity):
    dj_model = Sector
    table_class = EntitiesList
    window_class = EntityWindow
    table_fields = ['name']

    def build_form(self):
        layout = QVBoxLayout()
        layout_line = self.build_row('name')
        layout.addLayout(layout_line)
        return layout


class GUIHumanRelationType(GUIEntity):
    dj_model = HumanRelationType
    table_class = EntitiesList
    window_class = EntityWindow
    table_fields = ['name']

    def build_form(self):
        layout = QVBoxLayout()
        layout_line = self.build_row('name')
        layout.addLayout(layout_line)
        return layout


class GUITaskAim(GUIEntity):
    dj_model = TaskAim
    table_class = EntitiesList
    window_class = EntityWindow
    table_fields = ['name']

    def build_form(self):
        layout = QVBoxLayout()
        layout_line = self.build_row('name')
        layout.addLayout(layout_line)
        return layout


class GUIContactType(GUIEntity):
    dj_model = ContactType
    table_class = EntitiesList
    window_class = EntityWindow
    table_fields = ['name']

    def build_form(self):
        layout = QVBoxLayout()
        layout_line = self.build_row('name')
        layout.addLayout(layout_line)
        return layout


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
