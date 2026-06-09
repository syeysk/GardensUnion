import os
import sys
import django
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QTableView, QHeaderView, QLabel, QDialog, 
    QLineEdit, QDialogButtonBox, QAbstractItemView, QComboBox, QScrollArea, QCheckBox
)
from PyQt6.QtGui import QIntValidator
from PyQt6.QtCore import QAbstractTableModel, Qt, QModelIndex


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

# from django.conf import settings
from django.db.models import Q, ForeignKey, IntegerField, NOT_PROVIDED, BooleanField
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


class IntegerQField(QLineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setValidator(QIntValidator())
    
    def value(self):
        text = self.text().strip()
        return int(text) if text else None


class ForeignQField(QWidget):
    entity = None

    def __init__(self, gui_model, entity=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = QHBoxLayout()
        self.gui_model = gui_model

        self.btn_select = QPushButton()
        self.btn_select.clicked.connect(self.open_select_window)
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

    def open_select_window(self):
        window = SelectEntitywindow(self.gui_model)
        window.exec()
        if window.entity:
            self.set_entity(window.entity)


class SelectEntitywindow(QDialog):
    model = None

    def __init__(self, gui_model):
        super().__init__(None)
        screen = QApplication.primaryScreen().availableGeometry()
        self.setGeometry(0, 0, screen.width() // 3, 400)
        self.gui_model = gui_model
        table_view = EntitiesTable(func_click_on_entity=self.select_entity)
        table_view.set_model(self.gui_model)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(table_view)

        self.entity = None
    
    def select_entity(self, entity):
        self.entity = entity
        self.close()


class GUIEntity(QDialog):
    model = None
    links = tuple()

    def __init__(self, entity=None, preset_values=None):
        super().__init__(None)
        screen = QApplication.primaryScreen().availableGeometry()
        self.setGeometry(0, 0, screen.width() // 3, screen.height() - 30)
        self.preset_values = preset_values or {}
        self.inputs = {}
        self.entity = entity

        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)

        layout_form = self.build_form()
        self.set_entity(entity)
        layout.addLayout(layout_form)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if entity:
            layout.addLayout(self.build_links())

        # TODO: вынести в отдельный класс ScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(False)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)
        main_layout.setContentsMargins(0, 0, 0, 0)
        scroll_area.setWidget(central_widget)

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

            self.entity.save()
        else:
            print('create', data)
            entity = self.model.objects.create(**data)
            self.set_entity(entity)

        self.accept()
    
    def populate_form(self):
        for field_name, field in self.inputs.items():
            dj_field = self.model._meta.get_field(field_name)
            if self.entity:
                value = getattr(self.entity, field_name)
            else:
                if field_name in self.preset_values:
                    value = self.preset_values[field_name]
                else:
                    value = '' if dj_field.default is NOT_PROVIDED else dj_field.default
 
            if isinstance(field, QComboBox):
                field.setCurrentText(dict(dj_field.choices)[value])
            elif isinstance(field, QCheckBox):
                field.setChecked(value)
            elif isinstance(field, ForeignQField):
                field.set_entity(value)
            elif isinstance(field, QLineEdit):
                field.setText(str(value))

    def build_field_by_model(self, field_name):
        dj_field = self.model._meta.get_field(field_name)
        verbose = dj_field.verbose_name.capitalize()

        choices = dj_field.choices
        if choices:
            field = QComboBox()
            for choice_value, choice_name in choices:
                field.addItem(choice_name, choice_value)
        elif isinstance(dj_field, ForeignKey):
            field = ForeignQField(DJ2GUI[dj_field.remote_field.model])
        elif isinstance(dj_field, BooleanField):
            field = QCheckBox()
        elif isinstance(dj_field, IntegerField):
            field = IntegerQField()
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
            if isinstance(widget, IntegerQField):
                values[field] = widget.value()
            elif isinstance(widget, QLineEdit):
                values[field] = widget.text()
            elif isinstance(widget, ForeignQField):
                values[field] = widget.entity
            elif isinstance(widget, QCheckBox):
                values[field] = widget.isChecked()
            elif isinstance(widget, QComboBox):
                values[field] = widget.currentData()
            else:
                print('Unknown type of field:', widget, field)

        return values
    
    def build_form(self):
        raise NotImplemented()

    def build_links(self):
        layout = QVBoxLayout()
        for link_args, link_kwargs in self.links:
            table = LinkedEntitiesTable(self.entity, *link_args, **link_kwargs)
            layout.addLayout(table)
        
        return layout


class GUIHuman(GUIEntity):
    model = Human
    table_fields = ['family_name', 'first_name']
    links = (
        ((LinkContactHuman, 'contact'), {}),
        ((LinkHumanCommunity, 'community'), {}),
        ((LinkHumanMeeting, 'meeting'), {}),
        ((LinkTaskHuman, 'task'), {}),
        ((LinkHumanHuman, 'human_linked'), {'fields': ['relation']}),
    )

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
        return layout_fields


class GUICommunity(GUIEntity):
    model = Community
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
    model = Task
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
    model = Contact
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
    model = Meeting
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


class GUILinkedObject(GUIEntity):
    def __init__(self, model, table_fields, preset_values, *args, **kwargs):
        self.model = model
        self.table_fields = table_fields
        super().__init__(preset_values=preset_values, *args, **kwargs)

    def build_form(self):
        layout = QVBoxLayout()
        for field in self.model._meta.fields:
            if field.name == 'id':
                continue

            field_name = field.name
            layout_line = self.build_row(field_name)
            layout.addLayout(layout_line)

        return layout
    
    def __call__(self, entity=None):
        self.set_entity(entity)
        return self


class GUISector(GUIEntity):
    model = Sector
    table_fields = ['name']

    def build_form(self):
        layout = QVBoxLayout()
        layout_line = self.build_row('name')
        layout.addLayout(layout_line)
        return layout


class GUIHumanRelationType(GUIEntity):
    model = HumanRelationType
    table_fields = ['name']

    def build_form(self):
        layout = QVBoxLayout()
        layout_line = self.build_row('name')
        layout.addLayout(layout_line)
        return layout


class GUITaskAim(GUIEntity):
    model = TaskAim
    table_fields = ['name']

    def build_form(self):
        layout = QVBoxLayout()
        layout_line = self.build_row('name')
        layout.addLayout(layout_line)
        return layout


class GUIContactType(GUIEntity):
    model = ContactType
    table_fields = ['name']

    def build_form(self):
        layout = QVBoxLayout()
        layout_line = self.build_row('name')
        layout.addLayout(layout_line)
        return layout


DJ2GUI = {gui.model: gui for gui in GUIEntity.__subclasses__()}


class DjangoTableModel(QAbstractTableModel):
    def __init__(self, django_model, field_names, queryset=None, func_get_value=None):
        super().__init__()
        self.django_model = django_model
        self.field_names = field_names
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


class EntitiesTable(QVBoxLayout):
    def __init__(self, func_click_on_entity=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.table = QTableView()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.func_click_on_entity = func_click_on_entity
        self.table.doubleClicked.connect(self.open_edit_dialog)

        self.title_label = QLabel()
        self.title_label.setStyleSheet('font-size: 20px; font-weight: bold;')

        btn_add = QPushButton('Добавить')
        btn_add.clicked.connect(self.open_add_dialog)
        btn_delete = QPushButton('Удалить')
        btn_delete.clicked.connect(self.open_delete_dialog)

        header_layout = QHBoxLayout()
        header_layout.addWidget(self.title_label)
        header_layout.addWidget(btn_add)
        header_layout.addWidget(btn_delete)
        self.addLayout(header_layout)
        self.addWidget(self.table)
        # self.addWidget(btn_add, alignment=Qt.AlignmentFlag.AlignHCenter)
    
    def open_edit_dialog(self, index):
        def default_open_edit_dialog(entity):
            if self.gui_model(entity).exec() == QDialog.DialogCode.Accepted:
                self.table.model().refresh()

        entity = self.table.model().entities[index.row()]
        (self.func_click_on_entity or default_open_edit_dialog)(entity)

    def open_add_dialog(self):
        if self.gui_model().exec() == QDialog.DialogCode.Accepted:
            self.table.model().refresh()

    def open_delete_dialog(self, _):
        index = self.table.currentIndex()
        index_row = index.row()
        if index_row > -1:
            entity = self.table.model().entities[index.row()]
            entity.delete()
            self.table.model().refresh()
    
    def set_model(self, gui_model, *args):
        self.gui_model = gui_model
        model = DjangoTableModel(gui_model.model, gui_model.table_fields, *args)
        title = str(gui_model.model._meta.verbose_name_plural)
        self.title_label.setText(title)
        self.table.setModel(model)
        return title


class LinkedEntitiesTable(EntitiesTable):
    def __init__(self, entity, linking_table, item_slave, *args, fields=list(), **kwargs):
        super().__init__(*args, **kwargs)
        self.table.setFixedHeight(200)
        self.table.setMaximumHeight(200)
        self.table.setMinimumHeight(200)
        self.setContentsMargins(0, 50, 0, 0)

        item_main_model = entity.__class__
        item_main = item_main_model.__name__.lower()
        item_slave_model = linking_table._meta.get_field(item_slave).remote_field.model
        same = item_main_model is item_slave_model

        queryset = linking_table.objects
        if same:
            queryset = queryset.filter(Q(**{item_main: entity}) | Q(**{item_slave: entity}))
        else:
            queryset = queryset.filter(**{item_main: entity})

        def func_get_value(hyper_entity, field_name, field_value):
            if same and field_name == item_slave and field_value.pk == entity.pk:
                return getattr(hyper_entity, item_main)
                
            return field_value

        gui_model = GUILinkedObject(linking_table, [item_slave, *fields], {item_main: entity})
        self.set_model(gui_model, queryset, func_get_value)


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
        self.table_view = EntitiesTable()
        content_layout.addLayout(self.table_view)
        main_layout.addLayout(content_layout)
        self.update_table(GUIHuman)

    def update_table(self, gui_model):
        title = self.table_view.set_model(gui_model)
        self.setWindowTitle(title)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
