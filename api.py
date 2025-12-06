from pathlib import Path
from uuid import uuid4

from sqlalchemy import select, delete, create_engine, or_

from db import (
    Base,
    ContactType,
    HumanRelationType,
    Sector,
    TaskAim,
)

class Config:
    def __init__(self, base_dir):
        self._dbs_dir = base_dir / 'dbs'
        if not self._dbs_dir.exists():
            self._dbs_dir.mkdir()

        self._last_open_path = self._dbs_dir / 'last_open.txt'
        self.uuid = None
        self._db_dir = None
        self.path = None
        self.name = None
        self._db_name_path = None
        
        if not self._last_open_path.exists():
            self.make_new_db()

    def _populate_paths(self):
        self._db_dir = self._dbs_dir / self.uuid
        self.path = self._db_dir / 'sqlite3.db'
        self._db_name_path = self._db_dir / 'name.txt'

    def _set_uuid(self, uuid):
        self.uuid = uuid
        with self._last_open_path.open('w', encoding='utf-8') as last_open_file:
            last_open_file.write(self.uuid)

    def _set_last_uuid(self):
        with self._last_open_path.open(encoding='utf-8') as last_open_file:
            self.uuid = last_open_file.read()

    def make_new_db(self, name='Default'):
        """ Генерирует идентификатор новой базы и помечает её как последнюю открытую """
        self.name = name
        self._set_uuid(uuid4().hex)
        self._populate_paths()
        self._db_dir.mkdir()
        with self._db_name_path.open('w', encoding='utf-8') as db_name_file:
            db_name_file.write(name)

    def use_db(self, uuid=None):
        """Если uuid=None, то открывает базу, которая открывалась в прошлый раз"""
        if uuid:
            self._set_uuid(uuid)
        else:
            self._set_last_uuid()

        self._populate_paths()
        with self._db_name_path.open(encoding='utf-8') as db_name_file:
            self.name = db_name_file.read()

    def list_dbs(self):
        for db_dir in self._dbs_dir.iterdir():
            if db_dir.is_file():
                continue

            uuid = db_dir.name
            with (db_dir / 'name.txt').open(encoding='utf-8') as db_name_file:
                name = db_name_file.read()

            yield name, uuid


def get_engine_and_create_all(db_apth: Path):
    db_path_with_protocol = f'sqlite:///{db_apth}'
    engine = create_engine(db_path_with_protocol, echo=True)
    #engine = create_engine('sqlite://', echo=True)
    Base.metadata.create_all(engine)
    return engine


def create_first_rows(session):
    FIRST_ID = 1
    FIRST_NAME = 'Не указано'
    models = [ContactType, Sector, TaskAim, HumanRelationType]
    for model in models:
        query = select(model).where(model.id == FIRST_ID)
        if not session.scalars(query).first():
            entity = model(id=FIRST_ID, name=FIRST_NAME)
            session.add(entity)

    session.commit()

