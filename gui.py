import os
import sys
from datetime import date
from pathlib import Path

import gi
from jinja2 import Template

gi.require_version('Gtk', '4.0')
from gi.repository import GLib, Gio, Gtk, GObject, Gdk

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings') 
django.setup()

from django.conf import settings
from django.db.models import Q
from db.models import (
    BOOK_CONTACT_TYPES,
    BOOK_DID,
    CIRCLES,
    SEXES,
    CONTACT_STATUSES,
)
from db import models
from circle_map import CircleMapWindow

XML_DIR = settings.BASE_REPO_DIR / 'xml'
MENU_MAIN_PATH = XML_DIR / 'menu_main.xml'

FIELD_ID_SIZE = 30


class EntityEditWindow(Gtk.ApplicationWindow):
    entity_name = None
    entity_class = None

    def __init__(self, *args, entity_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.entity = None
        if entity_id:
            self.entity = self.entity_class.objects.filter(pk=entity_id).first()

        self.builder = WindowBuilder(XML_DIR / f'{self.entity_name}.xml', {'entity': self.entity}, parent_window=self)
        self.set_child(self.builder.root_widget)

    @GObject.Signal(arg_types=(int,))
    def entity_added(self, entity_id: int):
        pass

    @GObject.Signal(arg_types=(int, str, str))
    def entity_updated(self, entity_id: int, name: str, value: str):
        pass

    def on_change_any_data(self, field_entry, field_name: str):
        if isinstance(field_entry, Gtk.SpinButton):
            value = field_entry.get_value()
        elif isinstance(field_entry, Gtk.CheckButton):
            value = field_entry.props.active
        else:
            value = field_entry.get_text()
            
        self.change_any_data(field_name, value)

    def on_change_any_data_dropdown(self, dropdown, _pspec, field_name: str):
        item = dropdown.get_selected_item()
        self.change_any_data(field_name, item.item_id)

    def change_any_data(self, name: str, value):
        fields = {name: value}
        if self.entity:
            setattr(self.entity, name, value)
            self.entity.save()
            self.emit('entity_updated', self.entity.id, name, value)
        else:
            self.entity = self.entity_class(**fields)
            self.entity.save()
            self.builder.id_value.set_text(str(self.entity.id))            
            self.emit('entity_added', self.entity.id)


# Inspired by: https://www.reddit.com/r/GTK/comments/1889i8s/gtk4_python_how_to_set_columnview_header_labels/?tl=ru
class EntityColumnView:
    def _on_factory_setup(self, factory, list_item):
        cell = Gtk.Inscription()
        cell._binding = None
        list_item.set_child(cell)

    def _on_factory_bind(self, factory, list_item, what):
        cell = list_item.get_child()
        item = list_item.get_item()
        cell._binding = item.bind_property(what, cell, 'text', GObject.BindingFlags.SYNC_CREATE)

    def _on_factory_unbind(self, factory, list_item, what):
        cell = list_item.get_child()
        if cell._binding:
            cell._binding.unbind()
            cell._binding = None

    def _on_factory_teardown(self, factory, list_item):
        cell = list_item.get_child()
        cell._binding = None

    def __init__(self, parent_window, item_type, on_entity_added=None, on_entity_deleted=None, on_entity_selected=None):
        # Buttons

        self.parent_window = parent_window
        self.on_entity_added = on_entity_added
        self.on_entity_selected = on_entity_selected
        self.on_entity_deleted = on_entity_deleted

        buttons_box = Gtk.Box(spacing=6)
        buttons_box.props.orientation = Gtk.Orientation.HORIZONTAL
        
        if on_entity_deleted:
            delete_button = Gtk.Button(label='Удалить')
            delete_button.connect('clicked',self.on_delete_item_clicked)
            buttons_box.append(delete_button)

        if on_entity_added:
            add_button = Gtk.Button(label='Добавить')
            add_button.connect('clicked', self.on_add_item_clicked)
            buttons_box.append(add_button)

        if on_entity_selected:
            select_button = Gtk.Button(label='Выбрать')
            select_button.connect('clicked', self.on_select_item_clicked)            
            buttons_box.append(select_button)

        sign_label = Gtk.Label(label=f'{item_type.__gtype_name__} list')
        buttons_box.append(sign_label)

        # Item's list
    
        self.item_type_class = item_type
        self.list_store = Gio.ListStore(item_type=item_type)
        selection = Gtk.SingleSelection(model=self.list_store)
        view = Gtk.ColumnView(model=selection)
        view.connect('activate', self.on_activate_item)
        for field_title, field_name, size in item_type.columns:
            factory = Gtk.SignalListItemFactory()
            factory.connect('setup', self._on_factory_setup)
            factory.connect('bind', self._on_factory_bind, field_name)
            factory.connect('unbind', self._on_factory_unbind, field_name)
            factory.connect("teardown", self._on_factory_teardown)
            column = Gtk.ColumnViewColumn(title=field_title, factory=factory)
            if size:
                column.props.fixed_width = size
            else:
                column.props.expand = True

            view.append_column(column)

        self.box = Gtk.Box(spacing=2)
        self.box.props.orientation = Gtk.Orientation.VERTICAL
        self.box.append(buttons_box)
        self.box.append(view)
        self.selection = selection

    def append(self, db_object):
         self.list_store.append(self.item_type_class.from_db_object(db_object))

    def clear(self):
        self.list_store.remove_all()

    def open_adding_item_window(self, entity_id=None):
        window = self.item_type_class.window(
            transient_for=self.parent_window,
            title=self.item_type_class.__gtype_name__,
            modal=True,
            entity_id=entity_id,
        )
        window.connect('entity_added', self.on_entity_added)
        window.present()

    def on_activate_item(self, column_view, position):
        item = self.list_store.get_item(position)
        self.open_adding_item_window(item.entity_id)

    def on_add_item_clicked(self, _):
        self.open_adding_item_window()

    def on_select_item_clicked(self, _):
        window = EntityListToSelectWindow(
            entity_type_class=self.item_type_class,
            transient_for=self.parent_window,
            title=self.item_type_class.__gtype_name__,
            modal=True,
        )
        window.connect('entity_selected', self.on_entity_selected)
        window.present()

    def on_delete_item_clicked(self, _):
        selected_item = self.selection.props.selected_item
        self.on_entity_deleted(selected_item.entity_id)


class LinkedEntityColumnView(EntityColumnView):
    def __init__(self, parent_window, item_type, linking_table, item_main, item_slave, same=False):
        self.linking_table = linking_table
        self.item_main = item_main
        self.item_slave = item_slave
        self.same = same
        super().__init__(parent_window, item_type, self.on_entity_added, self.on_entity_deleted, self.on_entity_added)
        if self.parent_window.entity:
            self.update_list()

    def update_list(self):
        entity_id = self.parent_window.entity.id
        query = self.linking_table.objects
        if self.same:
            query = query.filter(Q(**{f'{self.item_main}_id': entity_id}) | Q(**{f'{self.item_slave}_id': entity_id}))
        else:
            query = query.filter(**{f'{self.item_main}_id': entity_id})

        for link in query.all():
            entity = getattr(link, self.item_slave)
            if self.same and entity.id == entity_id:
                entity = getattr(link, self.item_main)

            self.append(entity)

    def on_entity_added(self, widget, linked_entity_id):
        condition = {
            f'{self.item_main}_id': self.parent_window.entity.id,
            f'{self.item_slave}_id': linked_entity_id,
        }
        if not self.linking_table.objects.filter(**condition).first():
            kwargs = {f'{self.item_main}_id': self.parent_window.entity.id, f'{self.item_slave}_id': linked_entity_id}
            new_entity = self.linking_table(**kwargs)
            new_entity.save()
            self.clear()
            self.update_list()

    def on_entity_deleted(self, entity_id):
        condition = {
            f'{self.item_main}_id': self.parent_window.entity.id,
            f'{self.item_slave}_id': entity_id,
        }
        self.linking_table.objects.filter(**condition).delete()
        self.clear()
        self.update_list()


class SelectingEntityColumnView(EntityColumnView):
    def __init__(self, parent_window, item_type, on_entity_selected):
        super().__init__(parent_window, item_type, on_entity_selected=on_entity_selected)

    def on_activate_item(self, column_view, position):
        item = self.list_store.get_item(position)
        self.on_entity_selected(item.entity_id)


class EntityListWindow(Gtk.ApplicationWindow):
    def __init__(self, entity_type_class, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.entity_type_class = entity_type_class
        self.entity_db_class = getattr(models, entity_type_class.__gtype_name__)

        box = Gtk.Box()
        box.props.margin_top = 6
        box.props.margin_bottom = 6
        box.props.margin_start = 6
        box.props.margin_end = 6
        box.props.orientation = Gtk.Orientation.VERTICAL
        self.set_child(box)
        self.column_view = EntityColumnView(
            self,
            self.entity_type_class,
            self.on_entity_added,
            self.on_entity_deleted,
        )
        box.append(self.column_view.box)
        self.update_list()

    def on_entity_added(self, widget, _):
        self.column_view.clear()
        self.update_list()

    def on_entity_deleted(self, entity_id):
        self.entity_db_class.objects.filter(pk=entity_id).delete()
        self.column_view.clear()
        self.update_list()

    def update_list(self):
        for entity in self.entity_db_class.objects.all():
            self.column_view.append(entity)


class EntityListToSelectWindow(Gtk.ApplicationWindow):
    def __init__(self, entity_type_class, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.entity_type_class = entity_type_class
        self.entity_db_class = getattr(models, entity_type_class.__gtype_name__)

        box = Gtk.Box()
        box.props.margin_top = 6
        box.props.margin_bottom = 6
        box.props.margin_start = 6
        box.props.margin_end = 6
        box.props.orientation = Gtk.Orientation.VERTICAL
        self.set_child(box)
        self.column_view = SelectingEntityColumnView(
            self,
            self.entity_type_class,
            self.on_entity_selected,
        )
        box.append(self.column_view.box)
        for entity in self.entity_db_class.objects.all():
            self.column_view.append(entity)

    @GObject.Signal(arg_types=(int,))
    def entity_selected(self, entity_id: int):
        pass

    def on_entity_selected(self, selected_id):
        self.emit('entity_selected', selected_id)
        self.close()


class ItemDropDown(GObject.Object):
    __gtype_name__  = 'ItemDropDown'

    def __init__(self, item_id, name):
        super().__init__()
        self._item_id = item_id
        self._name = name

    @GObject.Property(type=int)
    def item_id(self):
        return self._item_id

    @GObject.Property(type=str)
    def name(self):
        return self._name


class UniDropDown(Gtk.DropDown):
    def __init__(self, tupples=None):
        super().__init__()
        factory = Gtk.SignalListItemFactory()
        factory.connect('setup', self._on_setup)
        factory.connect('bind', self._on_bind)
        self.store = Gio.ListStore.new(ItemDropDown)
        selection = Gtk.SingleSelection()
        selection.set_model(self.store)
        self.set_factory(factory)
        self.set_model(selection)
        
        if tupples:
            for item_id, item_name in tupples:
                self.append(item_id, item_name)

    def _on_setup(self, widget, item):
        """Setup the widget to show in the Gtk.Listview"""
        label = Gtk.Label()
        item.set_child(label)

    def _on_bind(self, widget, item):
        """bind data from the store object to the widget"""
        label = item.get_child()
        obj = item.get_item()
        label.set_text(obj.name)

    def append(self, item_id, item_name):
        self.store.append(ItemDropDown(item_id, item_name))


class WindowBuilder:
    def __init__(self, path_to_xml, context, parent_window=None):
        import xml.etree.ElementTree as ET
        self.parent_window = parent_window
        with open(path_to_xml, encoding='utf-8') as file_xml:
            template = Template(file_xml.read())
            templated_xml: str = template.render(context)

        root = ET.fromstring(templated_xml)
        self.parents = []
        self.root_widget = None
        self._go(root)
        
    def _go(self, node):
        tag = node.tag
        if tag == 'Row':
            data = self.parents[-1][2]
            data['x'] = 0
            data['y'] += 1
        else:
            if tag == 'EntityColumnView':
                gtkclass = LinkedEntityColumnView
            elif tag == 'UniDropDown':
                gtkclass = UniDropDown
            elif tag == 'Picture':
                gtkclass = Gtk.Picture.new_for_filename
            else:
                gtkclass = getattr(Gtk, tag)

            kwargs = {}

            if tag in ('Label', 'Button', 'CheckButton'):
                kwargs['label'] = node.text
            elif tag == 'Entry':
                kwargs['text'] = node.text
            elif tag == 'EntityColumnView':
                kwargs['parent_window'] = self.parent_window
                kwargs['item_type'] = globals()[node.attrib.pop('item_type')]
                kwargs['linking_table'] = getattr(models, node.attrib.pop('linking_table'))
                kwargs['item_main'] = node.attrib.pop('item_main')
                kwargs['item_slave'] = node.attrib.pop('item_slave')
                if 'same' in node.attrib:
                    kwargs['same'] = True
                    node.attrib.pop('same')
            elif tag == 'Picture':
                kwargs['filename'] = str(settings.BASE_REPO_DIR / node.attrib.pop('filename'))
            elif tag == 'Box':
                kwargs['orientation'] = getattr(Gtk.Orientation, node.attrib.pop('orientation', 'VERTICAL'))
            
            colspan = int(node.attrib.pop('colspan', '1'))

            gtkelem = gtkclass(**kwargs)
            for attr_name, attr_value in node.attrib.items():
                if attr_name == 'id':
                    setattr(self, attr_value, gtkelem)
                else:
                    if attr_name in {'selected', 'xalign', 'spacing', 'margin_top', 'margin_start', 'margin_bottom', 'margin_end', 'column_spacing', 'row_spacing'}:
                        attr_value = int(attr_value) if attr_value else 0

                    setattr(gtkelem.props, attr_name, attr_value)
        
            if self.parents:
                parent_gtk, parent_type, data = self.parents[-1]
                if parent_type == 'Grid':
                    if tag == 'EntityColumnView':
                        parent_gtk.attach(gtkelem.box, data['x'], data['y'], colspan, 1)
                        data['y'] += 6
                    else:
                        parent_gtk.attach(gtkelem, data['x'], data['y'], colspan, 1)

                    data['x'] += 1
                elif parent_type == 'Box':
                    if tag == 'EntityColumnView':
                        parent_gtk.append(gtkelem.box)
                    else:
                        parent_gtk.append(gtkelem)
                elif parent_type == 'ScrolledWindow':
                    if tag == 'EntityColumnView':
                        parent_gtk.set_child(gtkelem.box)
                    else:
                        parent_gtk.set_child(gtkelem)
        
            if tag == 'Grid':
                self.parents.append((gtkelem, tag, {'x': 0, 'y': -1}))
            elif tag == 'Box' or tag == 'ScrolledWindow':
                self.parents.append((gtkelem, tag, None))
            
            if not self.root_widget:
                self.root_widget = gtkelem

        for child in node:
            self._go(child)

        if tag in {'Grid', 'Box', 'ScrolledWindow'}:
            if self.parents:
                self.parents.pop(-1)


class HumanWindow(EntityEditWindow):
    entity_name = 'human'
    entity_class = models.Human

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        builder = self.builder

        # Top Left Controllers

        for item_id, item_name in SEXES.items():
            builder.sex_entry.append(item_id=item_id, item_name=item_name)

        builder.sex_entry.props.selected = (self.entity.sex - 1) if self.entity else 0
        builder.sex_entry.connect('notify::selected-item', self.on_change_any_data_dropdown, 'sex')

        birth_year_adjustment = Gtk.Adjustment(upper=3000, step_increment=1, page_increment=10)
        birth_month_adjustment = Gtk.Adjustment(upper=12, step_increment=1, page_increment=10)
        birth_day_adjustment = Gtk.Adjustment(upper=31, step_increment=1, page_increment=10)

        self.birth_year_entry = builder.birth_year_entry
        self.birth_year_entry.props.adjustment = birth_year_adjustment
        self.birth_year_entry.set_value(int(self.entity.birth_year) if self.entity else 0)
        self.birth_year_entry.connect('changed', self.on_change_birth_date)
        self.birth_year_entry.connect('changed', self.on_change_any_data, 'birth_year')

        self.birth_month_entry = builder.birth_month_entry
        self.birth_month_entry.props.adjustment = birth_month_adjustment
        self.birth_month_entry.set_value(int(self.entity.birth_month) if self.entity else 0)
        self.birth_month_entry.connect('changed', self.on_change_birth_date)
        self.birth_month_entry.connect('changed', self.on_change_any_data, 'birth_month')

        self.birth_day_entry = builder.birth_day_entry
        self.birth_day_entry.props.adjustment = birth_day_adjustment
        self.birth_day_entry.set_value(int(self.entity.birth_day) if self.entity else 0)
        self.birth_day_entry.connect('changed', self.on_change_birth_date)
        self.birth_day_entry.connect('changed', self.on_change_any_data, 'birth_day')

        self.age_value = builder.age_value

        # Top Right Controllers

        builder.family_name_entry.connect('changed', self.on_change_any_data, 'family_name')
        builder.first_name_entry.connect('changed', self.on_change_any_data, 'first_name')
        builder.father_name_entry.connect('changed', self.on_change_any_data, 'father_name')

        closing_adjustment = Gtk.Adjustment(upper=20, step_increment=1, page_increment=10)

        builder.closing_entry.props.adjustment = closing_adjustment
        builder.closing_entry.set_value(int(self.entity.closing) if self.entity else 0)
        builder.closing_entry.connect('changed', self.on_change_any_data, 'closing')
        
        for item_id, item_name in CIRCLES.items():
            builder.circle_entry.append(item_id=item_id, item_name=item_name)

        builder.circle_entry.props.selected = (self.entity.circle - 1) if self.entity else 0
        builder.circle_entry.connect('notify::selected-item', self.on_change_any_data_dropdown, 'circle')

        for sector in models.Sector.objects.all():
            builder.sector_entry.append(item_id=sector.id, item_name=sector.name)

        builder.sector_entry.props.selected = (self.entity.sector_id - 1) if self.entity else 0
        builder.sector_entry.connect('notify::selected-item', self.on_change_any_data_dropdown, 'sector_id')
        builder.sector_edit_button.connect('clicked', self.on_sector_edit_clicked)

        for item_id, item_name in BOOK_CONTACT_TYPES.items():
            builder.book_contact_type_entry.append(item_id=item_id, item_name=item_name)

        builder.book_contact_type_entry.props.selected = (self.entity.book_contact_type - 1) if self.entity else 0
        builder.book_contact_type_entry.connect('notify::selected-item', self.on_change_any_data_dropdown, 'book_contact_type')

        for item_id, item_name in BOOK_DID.items():
            builder.book_did_entry.append(item_id=item_id, item_name=item_name)

        builder.book_did_entry.props.selected = (self.entity.book_did - 1) if self.entity else 0
        builder.book_did_entry.connect('notify::selected-item', self.on_change_any_data_dropdown, 'book_did')

        # Bottom Controllers

        self.on_change_birth_date(None)

    def on_change_birth_date(self, spin_button):
        birth_date = date(
            self.birth_year_entry.get_value_as_int() or 1,
            self.birth_month_entry.get_value_as_int() or 1,
            self.birth_day_entry.get_value_as_int() or 1,
        )
        age_timedelta = date.today() - birth_date
        self.age_value.set_text(f'{age_timedelta.days // 365} лет')

    def on_sector_edit_clicked(self, button):
        window = EntityListWindow(Sector, transient_for=self, title='Sector List', modal=True)
        window.present()     


class ContactTypeWindow(EntityEditWindow):
    entity_name = 'contact_type'
    entity_class = models.ContactType

    def __init__(self, *args,  **kwargs):
        super().__init__(*args, **kwargs)
        self.builder.name_entry.connect('changed', self.on_change_any_data, 'name')


class SectorWindow(EntityEditWindow):
    entity_name = 'sector'
    entity_class = models.Sector

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.builder.name_entry.connect('changed', self.on_change_any_data, 'name')


class CommunityWindow(EntityEditWindow):
    entity_name = 'community'
    entity_class = models.Community

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.builder.name_entry.connect('changed', self.on_change_any_data, 'name')


class TaskWindow(EntityEditWindow):
    entity_name = 'task'
    entity_class = models.Task

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.builder.title_entry.connect('changed', self.on_change_any_data, 'title')
        self.builder.has_done.connect('toggled', self.on_change_any_data, 'has_done')
        self.builder.has_done.props.active = self.entity.has_done

        for task_aim in models.TaskAim.objects.all():
            self.builder.aim_entry.append(item_id=task_aim.id, item_name=task_aim.name)

        self.builder.aim_entry.props.selected = (self.entity.aim.id - 1) if self.entity else 0
        self.builder.aim_entry.connect('notify::selected-item', self.on_change_any_data_dropdown, 'aim_id')
        self.builder.aim_edit_button.connect('clicked', self.on_aim_edit_clicked)

    def on_aim_edit_clicked(self, button):
        window = EntityListWindow(TaskAim, transient_for=self, title='Task Aim List', modal=True)
        window.present()


class TaskAimWindow(EntityEditWindow):
    entity_name = 'task_aim'
    entity_class = models.TaskAim

    def __init__(self, *args,  **kwargs):
        super().__init__(*args, **kwargs)
        self.builder.name_entry.connect('changed', self.on_change_any_data, 'name')


class MeetingWindow(EntityEditWindow):
    entity_name = 'meeting'
    entity_class = models.Meeting

    def __init__(self, *args,  **kwargs):
        super().__init__(*args, **kwargs)
        self.builder.title_entry.connect('changed', self.on_change_any_data, 'title')
        #self.builder.description_entry.connect('changed', self.on_change_any_data, 'description')


class ContactWindow(EntityEditWindow):
    entity_name = 'contact'
    entity_class = models.Contact

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_default_size(400, 600)
        self.builder.value_entry.connect('changed', self.on_change_any_data, 'value')
        for contact_type in models.ContactType.objects.all():
            self.builder.type_entry.append(item_id=contact_type.id, item_name=contact_type.name)

        self.builder.type_entry.props.selected = (self.entity.type_id - 1) if self.entity else 0
        self.builder.type_entry.connect('notify::selected-item', self.on_change_any_data_dropdown, 'type_id')
        self.builder.type_edit_button.connect('clicked', self.on_type_edit_clicked)
        for item_id, item_name in CONTACT_STATUSES.items():
            self.builder.status_entry.append(item_id=item_id, item_name=item_name)

        self.builder.status_entry.props.selected = (self.entity.status - 1) if self.entity else 0
        self.builder.status_entry.connect('notify::selected-item', self.on_change_any_data_dropdown, 'status')
        
        from adapter import TGAdapter
        TGAdapter(self.builder.adapter_area, self.get_contact)

    def get_contact(self):
        return self.entity

    def on_type_edit_clicked(self, button):
        window = EntityListWindow(ContactType, transient_for=self, title='Contact Type List', modal=True)
        window.present()

 
class Human(GObject.Object):
    __gtype_name__  = 'Human'
    columns = (('ID', 'entity_id', FIELD_ID_SIZE), ('Фамилия', 'human_family_name', 150), ('Имя', 'human_first_name', 150))
    window = HumanWindow
    
    def __init__(self, entity_id, human_first_name, human_family_name):
        super().__init__()
        self._entity_id = entity_id
        self._human_first_name = human_first_name
        self._human_family_name = human_family_name

    @classmethod
    def from_db_object(cls, db_object):
        return cls(
            entity_id=db_object.id,
            human_first_name=db_object.first_name,
            human_family_name=db_object.family_name,
        )

    @GObject.Property(type=int)
    def entity_id(self):
        return self._entity_id

    @GObject.Property(type=str)
    def human_first_name(self):
        return self._human_first_name

    @GObject.Property(type=str)
    def human_family_name(self):
        return self._human_family_name


class Contact(GObject.Object):
    __gtype_name__  = 'Contact'
    columns = (('ID', 'entity_id', FIELD_ID_SIZE), ('Тип', 'contact_type', 80), ('Значение', 'contact_value', 150), ('Статус', 'contact_status', 150))
    window = ContactWindow

    def __init__(self, entity_id, contact_type, contact_value, contact_status):
        super().__init__()
        self._entity_id = entity_id
        self._contact_type = contact_type
        self._contact_value = contact_value
        self._contact_status = contact_status

    @classmethod
    def from_db_object(cls, db_object):
        return cls(
            entity_id=db_object.id,
            contact_type=db_object.type.name,
            contact_value=db_object.value,
            contact_status=CONTACT_STATUSES[db_object.status],
        )

    @GObject.Property(type=int)
    def entity_id(self):
        return self._entity_id

    @GObject.Property(type=str)
    def contact_type(self):
        return self._contact_type

    @GObject.Property(type=str)
    def contact_value(self):
        return self._contact_value

    @GObject.Property(type=str)
    def contact_status(self):
        return self._contact_status


class ContactType(GObject.Object):
    __gtype_name__  = 'ContactType'
    columns = (('ID', 'entity_id', FIELD_ID_SIZE), ('Название', 'contact_type_name', None))
    window = ContactTypeWindow
    
    def __init__(self, entity_id, contact_type_name):
        super().__init__()
        self._entity_id = entity_id
        self._contact_type_name = contact_type_name

    @classmethod
    def from_db_object(cls, db_object):
        return cls(
            entity_id=db_object.id,
            contact_type_name=db_object.name,
        )

    @GObject.Property(type=int)
    def entity_id(self):
        return self._entity_id

    @GObject.Property(type=str)
    def contact_type_name(self):
        return self._contact_type_name


class Sector(GObject.Object):
    __gtype_name__  = 'Sector'
    columns = (('ID', 'entity_id', FIELD_ID_SIZE), ('Название', 'sector_name', None))
    window = SectorWindow

    def __init__(self, entity_id, sector_name):
        super().__init__()
        self._entity_id = entity_id
        self._sector_name = sector_name

    @classmethod
    def from_db_object(cls, db_object):
        return cls(
            entity_id=db_object.id,
            sector_name=db_object.name,
        )

    @GObject.Property(type=int)
    def entity_id(self):
        return self._entity_id

    @GObject.Property(type=str)
    def sector_name(self):
        return self._sector_name


class Community(GObject.Object):
    __gtype_name__  = 'Community'
    columns =  (('ID', 'entity_id', FIELD_ID_SIZE), ('Название', 'community_name', None))
    window = CommunityWindow

    def __init__(self, entity_id, community_name):
        super().__init__()
        self._entity_id = entity_id
        self._community_name = community_name

    @classmethod
    def from_db_object(cls, db_object):
        return cls(
            entity_id=db_object.id,
            community_name=db_object.name,
        )

    @GObject.Property(type=int)
    def entity_id(self):
        return self._entity_id

    @GObject.Property(type=str)
    def community_name(self):
        return self._community_name


class Task(GObject.Object):
    __gtype_name__  = 'Task'
    columns =  (('ID', 'entity_id', FIELD_ID_SIZE), ('Сделано', 'has_done', 60), ('Название', 'task_title', 500))
    window = TaskWindow
    
    @classmethod
    def from_db_object(cls, db_object):
        return cls(
            entity_id=db_object.id,
            task_title=db_object.title,
            has_done=db_object.has_done,
        )

    def __init__(self, entity_id, task_title, has_done):
        super().__init__()
        self._entity_id = entity_id
        self._task_title = task_title
        self._has_done = has_done

    @GObject.Property(type=int)
    def entity_id(self):
        return self._entity_id

    @GObject.Property(type=str)
    def task_title(self):
        return self._task_title

    @GObject.Property(type=bool, default=False)
    def has_done(self):
        return self._has_done


class TaskAim(GObject.Object):
    __gtype_name__  = 'TaskAim'
    columns = (('ID', 'entity_id', FIELD_ID_SIZE), ('Название', 'task_aim_name', None))
    window = TaskAimWindow
    
    def __init__(self, entity_id, task_aim_name):
        super().__init__()
        self._entity_id = entity_id
        self._task_aim_name = task_aim_name

    @classmethod
    def from_db_object(cls, db_object):
        return cls(
            entity_id=db_object.id,
            task_aim_name=db_object.name,
        )

    @GObject.Property(type=int)
    def entity_id(self):
        return self._entity_id

    @GObject.Property(type=str)
    def task_aim_name(self):
        return self._task_aim_name


class Meeting(GObject.Object):
    __gtype_name__  = 'Meeting'
    columns = (('ID', 'entity_id', FIELD_ID_SIZE), ('Название', 'meeting_title', 400))
    window = MeetingWindow

    def __init__(self, entity_id, meeting_title):
        super().__init__()
        self._entity_id = entity_id
        self._meeting_title = meeting_title

    @classmethod
    def from_db_object(cls, db_object):
        return cls(
            entity_id=db_object.id,
            meeting_title=db_object.title,
        )

    @GObject.Property(type=int)
    def entity_id(self):
        return self._entity_id

    @GObject.Property(type=str)
    def meeting_title(self):
        return self._meeting_title


# Source: https://stackoverflow.com/questions/65807310/how-to-get-total-screen-size-in-python-gtk-without-using-deprecated-gdk-screen
def get_screen_size(display):
    mon_geoms = [monitor.get_geometry() for monitor in display.get_monitors()]
    x0 = min(r.x            for r in mon_geoms)
    y0 = min(r.y            for r in mon_geoms)
    x1 = max(r.x + r.width  for r in mon_geoms)
    y1 = max(r.y + r.height for r in mon_geoms)
    return x1 - x0, y1 - y0


class AppWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        x, y = get_screen_size(Gdk.Display.get_default())
        self.set_default_size(min(x, 600), y)
        self.props.show_menubar = True
        
        builder = WindowBuilder(XML_DIR / 'app.xml', {})
        self.set_child(builder.root_widget)

        builder.scrolled_widget.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        action_show_map = Gio.SimpleAction.new('show_map', None)
        action_show_map.connect('activate', self.on_show_map)
        self.add_action(action_show_map)

        builder.button_show_human.connect('clicked', self.on_show_entities, Human, models.Human)
        builder.button_show_community.connect('clicked', self.on_show_entities, Community, models.Community)
        builder.button_show_task.connect('clicked', self.on_show_entities, Task, models.Task)
        builder.button_show_contact.connect('clicked', self.on_show_entities, Contact, models.Contact)
        builder.button_show_meeting.connect('clicked', self.on_show_entities, Meeting, models.Meeting)

        self.main_box = builder.main_box
        self.entities_column_view = None
        self.on_show_entities(None, Human, models.Human)

    def on_show_entities(self, action, entity_class, entity_db_class):
        if self.entities_column_view:
            self.main_box.remove(self.entities_column_view.box)

        self.entities_column_view = EntityColumnView(
            self,
            entity_class,
            lambda widget, _: self.on_entity_added(widget, _, entity_db_class),
        )
        self.update_entity_list(entity_db_class)
        self.main_box.append(self.entities_column_view.box)

    def on_show_map(self, action, value):
        window = CircleMapWindow(transient_for=self, title='Circle Map', modal=True)
        window.present()

    def on_show_adding_entity(self, action, value=None):
        self.entities_column_view.open_item_window()

    def on_show_settings(self, action, value):
        pass

    def on_entity_added(self, widget, _, entity_db_class):
        self.entities_column_view.clear()
        self.update_entity_list(entity_db_class)

    def update_entity_list(self, entity_db_class):
        for entity in entity_db_class.objects.all():
            self.entities_column_view.append(entity)


class MyApplication(Gtk.Application):
    def __init__(self):
        super().__init__(application_id='org.syeysk.HumEnv')
        GLib.set_application_name('Human Environment Builder')

    def do_startup(self):
        Gtk.Application.do_startup(self)
        with open(MENU_MAIN_PATH, encoding='utf-8') as menu_main_file:
            builder = Gtk.Builder.new_from_string(menu_main_file.read(), -1)

        self.set_menubar(builder.get_object('menubar'))

    def do_activate(self):
        window = AppWindow(application=self, title='Human Environment')
        window.present()


app = MyApplication()
exit_status = app.run(sys.argv)
sys.exit(exit_status)
