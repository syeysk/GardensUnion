import datetime
from typing import List, Optional
from sqlalchemy import ForeignKey, String, select, insert, update, DateTime, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func

CIRCLE_DEVELOP = 1
CIRCLE_EFFECTIVITY = 2
CIRCLE_SUPPORT = 3
CIRCLES = {
    CIRCLE_DEVELOP: 'Развития',
    CIRCLE_EFFECTIVITY: 'Продуктивности', 
    CIRCLE_SUPPORT: 'Поддержки',
}

SEX_UNKNOWN = 1
SEX_MALE = 2
SEX_FEMALE = 3
SEXES = {
    SEX_UNKNOWN:  'Неизвестно',
    SEX_MALE: 'Мужчина',
    SEX_FEMALE:  'Женщина',
}

CONTACT_STATUS_ACTIVE = 1
CONTACT_STATUS_INACTIVE = 2
CONTACT_STATUS_DELETED = 3
CONTACT_STATUSES = {
    CONTACT_STATUS_ACTIVE: 'Активен',
    CONTACT_STATUS_INACTIVE: 'Неактивен',
    CONTACT_STATUS_DELETED: 'Удалён аккаунт',
}

BOOK_CONTACT_TYPE_UNKNOWN = 1
BOOK_CONTACT_TYPE_CONNECTOR = 2
BOOK_CONTACT_TYPE_CAPACITOR = 3
BOOK_CONTACT_TYPE_BRIDGE = 4
BOOK_CONTACT_TYPES = {
    BOOK_CONTACT_TYPE_UNKNOWN: 'Не указано',
    BOOK_CONTACT_TYPE_CONNECTOR: 'Коннектор',
    BOOK_CONTACT_TYPE_CAPACITOR: 'Конденсатор',
    BOOK_CONTACT_TYPE_BRIDGE: 'Мост',
}

BOOK_DID_UNKNOWN = 1
BOOK_DID_DANGEROUS = 2
BOOK_DID_INTERESTING = 3
BOOK_DID_DIFFICULT = 4
BOOK_DID = {
    BOOK_DID_UNKNOWN: 'Не указано',
    BOOK_DID_DANGEROUS: 'Опасен',
    BOOK_DID_INTERESTING: 'Интересен',
    BOOK_DID_DIFFICULT: 'Сложен',
}


class Base(DeclarativeBase):
    pass


class Sector(Base):
    __tablename__ = 'sector'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    humans: Mapped[List['Human']] = relationship(back_populates='sector', cascade='all, delete-orphan')


class Human(Base):
    __tablename__ = 'human'

    id: Mapped[int] = mapped_column(primary_key=True)
    family_name: Mapped[str] = mapped_column(String(100), nullable=False, default='')
    first_name: Mapped[str] = mapped_column(String(100), nullable=False, default='')
    father_name: Mapped[str] = mapped_column(String(100), nullable=False, default='')
    birth_year: Mapped[int] = mapped_column(nullable=False, default=0)
    birth_month: Mapped[int] = mapped_column(nullable=False, default=0)
    birth_day: Mapped[int] = mapped_column(nullable=False, default=0)
    circle: Mapped[int] = mapped_column(nullable=False, default=CIRCLE_DEVELOP)
    sex: Mapped[int] = mapped_column(nullable=False, default=SEX_UNKNOWN)
    closing: Mapped[int] = mapped_column(nullable=False, default=0)
    book_contact_type: Mapped[int] = mapped_column(nullable=False, default=BOOK_CONTACT_TYPE_UNKNOWN)
    book_did: Mapped[int] = mapped_column(nullable=False, default=BOOK_DID_UNKNOWN)

    sector_id: Mapped[int] = mapped_column(ForeignKey('sector.id'), nullable=False, default=1)
    sector: Mapped['Sector'] = relationship(back_populates='humans')


class ContactType(Base):
    __tablename__ = 'contact_type'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)


class Contact(Base):
    __tablename__ = 'contact'

    id: Mapped[int] = mapped_column(primary_key=True)
    value: Mapped[str] = mapped_column(String(100), nullable=False, default='')
    type_id: Mapped[int] = mapped_column(ForeignKey('contact_type.id'), nullable=False, default=1)
    type: Mapped['ContactType'] = relationship()
    status: Mapped[int] = mapped_column(nullable=False, default=CONTACT_STATUS_ACTIVE)
    data: Mapped[JSON] = mapped_column(type_=JSON, nullable=False, default=dict)


class Community(Base):
    __tablename__ = 'community'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)


class Task(Base):
    __tablename__ = 'task'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    aim_id: Mapped[int] = mapped_column(ForeignKey('task_aim.id'), nullable=False, default=1)
    aim: Mapped['TaskAim'] = relationship()
    has_done: Mapped[bool] = mapped_column(nullable=False, default=False)


class Meeting(Base):
    __tablename__ = 'meeting'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(10000), nullable=False, default='')
    date: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TaskAim(Base):
    __tablename__ = 'task_aim'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)


class LinkContactHuman(Base):
    __tablename__ = 'link_contact_human'

    id: Mapped[int] = mapped_column(primary_key=True)
    contact_id: Mapped[int] = mapped_column(ForeignKey('contact.id'), nullable=False)
    human_id: Mapped[int] = mapped_column(ForeignKey('human.id'), nullable=False)
    contact: Mapped['Contact'] = relationship()
    human: Mapped['Human'] = relationship()


class LinkContactCommunity(Base):
    __tablename__ = 'link_contact_community'

    id: Mapped[int] = mapped_column(primary_key=True)
    contact_id: Mapped[int] = mapped_column(ForeignKey('contact.id'), nullable=False)
    community_id: Mapped[int] = mapped_column(ForeignKey('community.id'), nullable=False)
    contact: Mapped['Contact'] = relationship()
    community: Mapped['Community'] = relationship()


class LinkTaskHuman(Base):
    __tablename__ = 'link_task_human'

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey('task.id'), nullable=False)
    human_id: Mapped[int] = mapped_column(ForeignKey('human.id'), nullable=False)
    task: Mapped['Task'] = relationship()
    human: Mapped['Human'] = relationship()


class LinkTaskCommunity(Base):
    __tablename__ = 'link_task_community'

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey('task.id'), nullable=False)
    community_id: Mapped[int] = mapped_column(ForeignKey('community.id'), nullable=False)
    task: Mapped['Task'] = relationship()
    community: Mapped['Community'] = relationship()


class LinkTaskMeeting(Base):
    __tablename__ = 'link_task_meeting'

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey('task.id'), nullable=False)
    meeting_id: Mapped[int] = mapped_column(ForeignKey('meeting.id'), nullable=False)
    task: Mapped['Task'] = relationship()
    meeting: Mapped['Meeting'] = relationship()


class LinkHumanCommunity(Base):
    __tablename__ = 'link_human_community'

    id: Mapped[int] = mapped_column(primary_key=True)
    human_id: Mapped[int] = mapped_column(ForeignKey('human.id'), nullable=False)
    community_id: Mapped[int] = mapped_column(ForeignKey('community.id'), nullable=False)
    human: Mapped['Human'] = relationship()
    community: Mapped['Community'] = relationship()


class LinkHumanMeeting(Base):
    __tablename__ = 'link_human_meeting'

    id: Mapped[int] = mapped_column(primary_key=True)
    human_id: Mapped[int] = mapped_column(ForeignKey('human.id'), nullable=False)
    meeting_id: Mapped[int] = mapped_column(ForeignKey('meeting.id'), nullable=False)
    human: Mapped['Human'] = relationship()
    meeting: Mapped['Meeting'] = relationship()


class HumanRelationType(Base):
    __tablename__ = 'human_relation_type'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)


class LinkHumanHuman(Base):
    __tablename__ = 'link_human_human'

    id: Mapped[int] = mapped_column(primary_key=True)
    human_id: Mapped[int] = mapped_column(ForeignKey('human.id'), nullable=False)
    human_linked_id: Mapped[int] = mapped_column(ForeignKey('human.id'), nullable=False)
    relation_id: Mapped[int] = mapped_column(ForeignKey('human_relation_type.id'), nullable=False, default=1)
    human: Mapped['Human'] = relationship(foreign_keys=[human_id])
    human_linked: Mapped['Human'] = relationship(foreign_keys=[human_linked_id])
    relation: Mapped['HumanRelationType'] = relationship()
