import os
import sys
import django
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QTableView, QHeaderView, QLabel, QDialog, 
    QLineEdit, QFormLayout, QDialogButtonBox, QAbstractItemView, QComboBox, QScrollArea
)
from PyQt6.QtCore import QAbstractTableModel, Qt, QModelIndex


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

# from django.conf import settings
from django.db.models import Q
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

    HumanRelationType,
    Sector,
)


class ForeignField(QWidget):
    entity = None

    def __init__(self, gui_model, entity=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = QHBoxLayout()
        self.gui_model = gui_model

        self.btn_select = QPushButton()
        layout.addWidget(self.btn_select)

        self.btn_edit = QPushButton('o')
        self.btn_edit.clicked.connect(self.open_entity_window)
        layout.addWidget(self.btn_edit)

        self.setLayout(layout)
        self.set_entity(entity)
    
    def set_entity(self, entity):
        self.entity = entity
        self.btn_select.setText(str(entity))

    def open_entity_window(self):
        if self.entity:
            if self.gui_model(self.entity).exec() == QDialog.DialogCode.Accepted:
                self.btn_select.setText(str(self.entity))


class GUIEntity(QDialog):
    model = None

    def __init__(self, entity=None):
        super().__init__(None)
        screen = QApplication.primaryScreen().availableGeometry()
        self.setGeometry(0, 0, screen.width() // 3, screen.height() - 30)

        self.inputs = {}

        main_layout = QVBoxLayout(self)
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setLayout(layout)
        main_layout.addWidget(scroll_area)

        self.form_layout = QFormLayout()

        self.entity = entity
        layout_form = self.build_form()
        self.set_entity(entity)
        layout.addLayout(layout_form)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def set_entity(self, entity):
        self.entity = entity
        title_prefix = 'Редактировать' if entity else 'Добавить'
        self.setWindowTitle(f'{title_prefix}: {self.model._meta.verbose_name}')
        self.populate_form()

    def save(self):
        data = self.get_data()
        if self.entity:
            print('update', data)
            for field, value in data.items():
                setattr(self.entity, field, value)

            #self.entity.save()
        else:
            print('create', data)
            entity = self.model.objects.create(**data)
            self.set_entity(entity)

        self.accept()
    
    def populate_form(self):
        if not self.entity:
            return

        for field_name, field in self.inputs.items():
            dj_field = self.model._meta.get_field(field_name)
            if isinstance(field, QComboBox):
                value = getattr(self.entity, field_name)
                field.setCurrentText(dict(dj_field.choices)[value])
            elif isinstance(field, ForeignField):
                value = getattr(self.entity, field_name)
                field.set_entity(value)
            elif isinstance(field, QLineEdit):
                value = getattr(self.entity, field_name)
                field.setText(str(value))

    def build_field_by_model(self, field_name):
        from django.db.models import ForeignKey
        dj_field = self.model._meta.get_field(field_name)
        verbose = dj_field.verbose_name.capitalize()

        choices = dj_field.choices
        if choices:
            field = QComboBox()
            for choice_value, choice_name in choices:
                field.addItem(choice_name, choice_value)
        elif isinstance(dj_field, ForeignKey):
            field = ForeignField(DJ2GUI[dj_field.remote_field.model])
        else:
            field = QLineEdit()

        self.inputs[field_name] = field
        return QLabel(f'{verbose}:'), field

    def build_row(self, field_name):
        label, edit = self.build_field_by_model(field_name)
        layout_line = QHBoxLayout()
        layout_line.addWidget(label)
        layout_line.addWidget(edit)
        return layout_line

    def get_data(self):
        values = {}
        for field, widget in self.inputs.items():
            if isinstance(widget, QLineEdit):
                values[field] = widget.text()
            elif isinstance(widget, ForeignField):
                values[field] = widget.entity
            elif isinstance(widget, QComboBox):
                values[field] = widget.currentData()

        return values
    
    def build_form(self):
        raise NotImplemented()


class GUIHuman(GUIEntity):
    model = Human
    table_fields = ['id', 'family_name', 'first_name']

    def build_form(self):
        entity = self.entity
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
        layout_links = QVBoxLayout()
        if entity:
            table = LinkedEntitiesTable(entity, LinkContactHuman, 'contact')
            layout_links.addWidget(table)
            table = LinkedEntitiesTable(entity, LinkHumanCommunity, 'community')
            layout_links.addWidget(table)
            table = LinkedEntitiesTable(entity, LinkHumanMeeting, 'meeting')
            layout_links.addWidget(table)
            table = LinkedEntitiesTable(entity, LinkTaskHuman, 'task')
            layout_links.addWidget(table)
            table = LinkedEntitiesTable(entity, LinkHumanHuman, 'human_linked', fields=['relation'], same=True)
            layout_links.addWidget(table)

        layout = QVBoxLayout()
        layout.addLayout(layout_fields)
        layout.addLayout(layout_links)
        return layout


class GUICommunity(GUIEntity):
    model = Community
    table_fields = ['id', 'name']

    def build_form(self):
        entity = self.entity
        layout = QVBoxLayout()
        field_names = ['name']
        for field_name in field_names:
            layout_line = self.build_row(field_name)
            layout.addLayout(layout_line)
        
        if entity:
            table = LinkedEntitiesTable(entity, LinkHumanCommunity, 'human')
            layout.addWidget(table)
            table = LinkedEntitiesTable(entity, LinkContactCommunity, 'contact')
            layout.addWidget(table)
            table = LinkedEntitiesTable(entity, LinkTaskCommunity, 'task')
            layout.addWidget(table)

        return layout


class GUITask(GUIEntity):
    model = Task
    table_fields = ['id', 'has_done', 'title']

    def build_form(self):
        entity = self.entity
        layout = QVBoxLayout()

        if entity:
            table = LinkedEntitiesTable(entity, LinkTaskHuman, 'human')
            layout.addWidget(table)
            table = LinkedEntitiesTable(entity, LinkTaskCommunity, 'community')
            layout.addWidget(table)
            table = LinkedEntitiesTable(entity, LinkTaskMeeting, 'meeting')
            layout.addWidget(table)

        return layout


class GUIContact(GUIEntity):
    model = Contact
    table_fields = ['id', 'type', 'value', 'status']

    def build_form(self):
        entity = self.entity
        layout = QVBoxLayout()

        if entity:
            table = LinkedEntitiesTable(entity, LinkContactHuman, 'human')
            layout.addWidget(table)
            table = LinkedEntitiesTable(entity, LinkContactCommunity, 'community')
            layout.addWidget(table)

        return layout


class GUIMeeting(GUIEntity):
    model = Meeting
    table_fields = ['id', 'title']

    def build_form(self):
        entity = self.entity
        layout = QVBoxLayout()

        if entity:
            table = LinkedEntitiesTable(entity, LinkHumanMeeting, 'human')
            layout.addWidget(table)
            table = LinkedEntitiesTable(entity, LinkTaskMeeting, 'task')
            layout.addWidget(table)

        return layout


class GUILinkedObject(GUIEntity):
    def __init__(self, model, table_fields, *args, **kwargs):
        self.model = model
        self.table_fields = table_fields
        super().__init__(*args, **kwargs)

    def build_form(self):
        layout = QVBoxLayout()
        # TODO: автоматически собирать поля с django-модели
        for field in self.model._meta.fields:
            field_name = field.name
            layout_line = self.build_row(field_name)
            layout.addLayout(layout_line)

        return layout
    
    def __call__(self, entity=None):
        self.set_entity(entity)
        return self


class GUISector(GUIEntity):
    model = Sector
    table_fields = ['id', 'name']

    def build_form(self):
        layout = QVBoxLayout()
        layout_line = self.build_row('name')
        layout.addLayout(layout_line)
        return layout


class GUIHumanRelationType(GUIEntity):
    model = HumanRelationType
    table_fields = ['id', 'name']

    def build_form(self):
        layout = QVBoxLayout()
        layout_line = self.build_row('name')
        layout.addLayout(layout_line)
        return layout


DJ2GUI = {gui.model: gui for gui in GUIEntity.__subclasses__()}


class DjangoTableModel(QAbstractTableModel):
    def __init__(self, django_model, field_names, gui_model, queryset=None, func_get_value=None):
        super().__init__()
        self.django_model = django_model
        self.gui_model = gui_model
        self.field_names = gui_model.table_fields
        self._headers = []
        self._data = []
        self.entities = []
        self.queryset = django_model.objects if queryset is None else queryset 
        self.func_get_value = func_get_value
        for name in field_names:
            if name == 'id':
                self._headers.append('ID')
            else:
                self._headers.append(django_model._meta.get_field(name).verbose_name.capitalize())

        self.refresh()

    def refresh(self):
        self.beginResetModel()
        _data = self.queryset.only(*self.field_names)
        self._data = []
        self.entities = []
        for entity in _data:
            self.entities.append(entity)
            row = []
            for name in self.field_names:
                value = getattr(entity, name)
                row.append(self.func_get_value(entity, name, value) if self.func_get_value else value)

            self._data.append(row)

        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):  # TODO: узнать, что это за аргумент parent
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self.field_names)
    
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            return str(self._data[index.row()][index.column()])

        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self._headers[section]

        return None


class EntitiesTable(QTableView):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.doubleClicked.connect(self.open_edit_dialog)

    def open_add_dialog(self):
        table_model = self.model()
        if table_model.gui_model().exec() == QDialog.DialogCode.Accepted:
            self.model().refresh()

    def open_edit_dialog(self, index):
        table_model = self.model()
        entity = table_model.entities[index.row()]
        # entity = table_model.django_model.objects.get(id=record_id)
        if table_model.gui_model(entity).exec() == QDialog.DialogCode.Accepted:
            self.model().refresh()


class LinkedEntitiesTable(EntitiesTable):
    def __init__(self, entity, linking_table, item_slave, *args, fields=list(), same=False, **kwargs):
        super().__init__(None, *args, **kwargs)
        self.setFixedHeight(200)

        item_main = entity.__class__.__name__.lower()
        # item_slave_type = linking_table.meta.fields 

        queryset = linking_table.objects
        if same:
            queryset = queryset.filter(Q(**{item_main: entity}) | Q(**{item_slave: entity}))#.annotate(linked_id=case)
        else:
            queryset = queryset.filter(**{item_main: entity})

        def func_get_value(hyper_entity, field_name, field_value):
            if same and field_name == item_slave and field_value.pk == entity.pk:
                return getattr(hyper_entity, item_main)
                
            return field_value

        gui_model = GUILinkedObject(linking_table, ['id', item_slave, *fields])
        model = DjangoTableModel(linking_table, gui_model.table_fields, gui_model, queryset, func_get_value)
        self.setModel(model)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        screen = QApplication.primaryScreen().availableGeometry()
        self.setGeometry(0, 0, screen.width() // 2, screen.height() - 30)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        def f(gui_model):
            def _f():
                self.update_table(gui_model)
            
            return _f

        # 1. ЛЕВАЯ ПАНЕЛЬ
        side_panel = QVBoxLayout()
        gui_models = [GUIHuman, GUICommunity, GUITask, GUIContact, GUIMeeting]
        for gui_model in gui_models:
            btn = QPushButton(gui_model.model._meta.verbose_name)
            btn.setFixedWidth(120)
            btn.clicked.connect(f(gui_model))
            side_panel.addWidget(btn)

        side_panel.addStretch()
        main_layout.addLayout(side_panel)

        # 2. ПРАВАЯ ЧАСТЬ (ТАБЛИЦА)
        content_layout = QVBoxLayout()
        
        self.title_label = QLabel('Заголовок')
        self.title_label.setStyleSheet('font-size: 20px; font-weight: bold;')
        content_layout.addWidget(self.title_label)

        self.table_view = EntitiesTable(self)
        content_layout.addWidget(self.table_view)

        self.add_button = QPushButton('Добавить')
        self.add_button.setFixedWidth(200)
        self.add_button.clicked.connect(self.table_view.open_add_dialog)
        content_layout.addWidget(self.add_button, alignment=Qt.AlignmentFlag.AlignHCenter)

        main_layout.addLayout(content_layout)

        self.update_table(GUIHuman)

    def update_table(self, gui_model):
        django_model = gui_model.model
        model = DjangoTableModel(django_model, gui_model.table_fields, gui_model)
        title = str(django_model._meta.verbose_name_plural)
        self.table_view.setModel(model)
        self.title_label.setText(title)
        self.setWindowTitle(title)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
