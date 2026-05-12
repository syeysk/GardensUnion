import os
import sys
import django
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QTableView, QHeaderView, QLabel, QDialog, 
    QLineEdit, QFormLayout, QDialogButtonBox, QAbstractItemView, QComboBox
)
from PyQt6.QtCore import QAbstractTableModel, Qt, QModelIndex


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

# from django.conf import settings
# from django.db.models import Q
# from db.models import (
#     BOOK_CONTACT_TYPES,
#     BOOK_DID,
#     CIRCLES,
#     SEXES,
#     CONTACT_STATUSES,
# )
from db.models import Community, Contact, Human, Task, Meeting


class GUI:
    def __init__(self):
        self.inputs = {}

    def build_field_by_model(self, field_name, model, entity):
        dj_field = model._meta.get_field(field_name)
        verbose = dj_field.verbose_name.capitalize()

        choices = dj_field.choices
        if choices:
            field = QComboBox()
            for choice_value, choice_name in choices:
                field.addItem(choice_name, choice_value)
            
            if entity:
                value = getattr(entity, field_name)
                field.setCurrentText(dict(choices)[value])
        else:
            field = QLineEdit()
            if entity:
                value = getattr(entity, field_name)
                field.setText(str(value))

        self.inputs[field_name] = field
        return QLabel(verbose), field

    def build_row(self, field_name, model_class, entity):
        label, edit = self.build_field_by_model(field_name, model_class, entity)
        layout_line = QHBoxLayout()
        layout_line.addWidget(label)
        layout_line.addWidget(edit)
        return layout_line


class GUIHuman(GUI):
    model = Human
    table_fields = ['id', 'family_name', 'first_name']

    def build_form(self, entity=dict()):
        layout_left = QVBoxLayout()
        field_names = ['sex', 'birth_year', 'birth_month', 'birth_day']
        for field_name in field_names:
            layout_line = self.build_row(field_name, self.model, entity)
            layout_left.addLayout(layout_line)

        layout_right = QVBoxLayout()
        field_names = ['family_name', 'first_name', 'father_name', 'closing', 'circle', 'sector', 'book_contact_type', 'book_did']
        for field_name in field_names:
            layout_line = self.build_row(field_name, self.model, entity)
            layout_right.addLayout(layout_line)

        layout = QHBoxLayout()
        layout.addLayout(layout_left)
        layout.addLayout(layout_right)
        return layout


class GUICommunity(GUI):
    model = Community
    table_fields = ['id', 'name']

    def build_form(self, entity=dict()):
        layout = QVBoxLayout()
        field_names = ['name']
        for field_name in field_names:
            layout_line = self.build_row(field_name, self.model, entity)
            layout.addLayout(layout_line)
        
        return layout


class GUITask(GUI):
    model = Task
    table_fields = ['id', 'has_done', 'title']

    def build_form(self, entity=dict()):
        layout = QVBoxLayout()
        return layout


class GUIContact(GUI):
    model = Contact
    table_fields = ['id', 'type', 'value', 'status']

    def build_form(self, entity=dict()):
        layout = QVBoxLayout()
        return layout


class GUIMeeting(GUI):
    model = Meeting
    table_fields = ['id', 'title']

    def build_form(self, entity=dict()):
        layout = QVBoxLayout()
        return layout


class DjangoTableModel(QAbstractTableModel):
    def __init__(self, django_model, field_names):
        super().__init__()
        self.django_model = django_model
        self.field_names = field_names
        self._headers = []
        for name in field_names:
            if name == 'id':
                self._headers.append('ID')
            else:
                self._headers.append(django_model._meta.get_field(name).verbose_name.capitalize())

        self.refresh()

    def refresh(self):
        self.beginResetModel()
        self._data = list(self.django_model.objects.values_list(*self.field_names))
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


class RecordDialog(QDialog):
    def __init__(self, parent, gui_model, entity=None):
        super().__init__(parent)
        self.gui_model = gui_model

        title_prefix = 'Редактировать' if entity else 'Добавить'
        self.setWindowTitle(f'{title_prefix}: {gui_model.model._meta.verbose_name}')
        layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()

        layout_form = gui_model.build_form(entity)
        layout.addLayout(layout_form)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self):
        values = {}
        for field, widget in self.gui_model.inputs.items():
            if isinstance(widget, QLineEdit):
                values[field] = widget.text()
            elif isinstance(widget, QComboBox):
                values[field] = widget.currentData()

        return values


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        screen = QApplication.primaryScreen().availableGeometry()
        self.setGeometry(0, 0, screen.width() // 2, screen.height() - 30)
        
        self.current_model_class = Human

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

        self.table_view = QTableView()
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_view.doubleClicked.connect(self.open_edit_dialog)
        content_layout.addWidget(self.table_view)

        self.add_button = QPushButton('Добавить')
        self.add_button.setFixedWidth(200)
        self.add_button.clicked.connect(self.open_add_dialog)
        content_layout.addWidget(self.add_button, alignment=Qt.AlignmentFlag.AlignHCenter)

        main_layout.addLayout(content_layout)

        self.update_table(GUIHuman)

    def update_table(self, gui_model):
        self.current_model_class = gui_model()
        django_model = gui_model.model
        model = DjangoTableModel(django_model, gui_model.table_fields)
        self.table_view.setModel(model)
        self.title_label.setText(str(django_model._meta.verbose_name_plural))
        self.setWindowTitle(str(django_model._meta.verbose_name_plural))

    def open_add_dialog(self):
        dialog = RecordDialog(self, self.current_model_class)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.current_model_class.model.objects.create(**data)
            self.table_view.model().refresh() # Обновляем таблицу

    def open_edit_dialog(self, index):
        # Получаем ID из первой колонки выбранной строки
        row = index.row()
        record_id = self.table_view.model()._data[row][0]

        entity = self.current_model_class.model.objects.get(id=record_id)

        # Открываем диалог с данными
        dialog = RecordDialog(self, self.current_model_class, entity)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_data = dialog.get_data()
            for field, value in new_data.items():
                setattr(entity, field, value)

            entity.save()
            self.table_view.model().refresh()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
