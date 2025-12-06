from django.conf import settings
from django.db import models

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


class Sector(models.Model):
    name = models.CharField('Наименование', max_length=64, unique=True)
    
    class Model:
        verbose_name = 'Сектор'
        verbose_name_plural = 'Секторы'


class Human(models.Model):
    family_name = models.CharField('Фамилия', max_length=100, blank=True)
    first_name = models.CharField('Имя', max_length=100, blank=True)
    father_name = models.CharField('Отчество', max_length=100, blank=True)
    birth_year = models.IntegerField('Год рождения', default=0)
    birth_month = models.IntegerField('Месяц рождения', default=0)
    birth_day = models.IntegerField('День рождения', default=0)
    circle = models.IntegerField('Круг', choices=CIRCLES, default=CIRCLE_DEVELOP)
    sex = models.IntegerField('Пол', choices=SEXES, default=SEX_UNKNOWN)
    closing = models.IntegerField('Близость', default=0)
    book_contact_type = models.IntegerField('Тип контакта', choices=BOOK_CONTACT_TYPES, default=BOOK_CONTACT_TYPE_UNKNOWN)
    book_did = models.IntegerField('', choices=BOOK_DID, default=BOOK_DID_UNKNOWN)

    sector = models.ForeignKey(Sector, on_delete=models.CASCADE, related_name='humans')

    class Model:
        verbose_name = 'Человек'
        verbose_name_plural = 'Люди'


class ContactType(models.Model):
    name = models.CharField('Наименование', max_length=100, unique=True)
    
    class Model:
        verbose_name = 'Тип контакта'
        verbose_name_plural = 'Типы контактов'


class Contact(models.Model):
    value = models.CharField('Значение', max_length=100, blank=True)
    type = models.ForeignKey(ContactType, on_delete=models.CASCADE)
    status = models.IntegerField('Статус', choices=CONTACT_STATUSES, default=CONTACT_STATUS_ACTIVE)
    data = models.JSONField(default=dict)

    class Model:
        verbose_name = 'Контакт'
        verbose_name_plural = 'Контакты'


class Community(models.Model):
    name = models.CharField('Наименование', max_length=100)
    
    class Model:
        verbose_name = 'Сообщество'
        verbose_name_plural = 'Сообщества'


class TaskAim(models.Model):
    name = models.CharField('Наименование', max_length=100)

    class Model:
        verbose_name = 'Цель задачи'
        verbose_name_plural = 'Цели задачи'


class Task(models.Model):
    title = models.CharField('Название', max_length=100)
    aim = models.ForeignKey(TaskAim, on_delete=models.CASCADE)
    has_done = models.BooleanField('Выполнена?', default=False)
    
    class Model:
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'


class Meeting(models.Model):
    title = models.CharField('Заголовок', max_length=100)
    description = models.CharField('Описание', max_length=10000, blank=True, default='')
    date = models.DateTimeField(auto_now_add=True)

    class Model:
        verbose_name = 'Встреча'
        verbose_name_plural = 'Встречи'


class LinkContactHuman(models.Model):
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE)
    human = models.ForeignKey(Human, on_delete=models.CASCADE)


class LinkContactCommunity(models.Model):
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE)
    community = models.ForeignKey(Community, on_delete=models.CASCADE)


class LinkTaskHuman(models.Model):
    human = models.ForeignKey(Human, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)


class LinkTaskCommunity(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    community = models.ForeignKey(Community, on_delete=models.CASCADE)


class LinkTaskMeeting(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE)


class LinkHumanCommunity(models.Model):
    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    human = models.ForeignKey(Human, on_delete=models.CASCADE)


class LinkHumanMeeting(models.Model):
    human = models.ForeignKey(Human, on_delete=models.CASCADE)
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE)


class HumanRelationType(models.Model):
    name = models.CharField('Наименование', max_length=100)

    class Model:
        verbose_name = 'Тип отношений'
        verbose_name_plural = 'Типы отношений'


class LinkHumanHuman(models.Model):
    human = models.ForeignKey(Human, on_delete=models.CASCADE)
    human_linked = models.ForeignKey(Human, on_delete=models.CASCADE, related_name='humans_linked')
    relation = models.ForeignKey(HumanRelationType, on_delete=models.CASCADE)
