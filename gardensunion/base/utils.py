from django.conf import settings
from django.core.exceptions import FieldDoesNotExist


def get_dj_model(entity_type_code=None):
    if not settings.ENTITY_MODELS_BY_CODE:
        print('+++ created')
        for gui_model_str in settings.ENTITY_TYPES:
            names_list = gui_model_str.split('.')
            package_list, gui_model_name = '.'.join(names_list[:-1]), names_list[-1]
            package = __import__(package_list, fromlist=[gui_model_name])
            gui_model = getattr(package, gui_model_name)
            settings.ENTITY_MODELS_BY_CODE[gui_model.dj_model.CODE] = gui_model

    return settings.ENTITY_MODELS_BY_CODE.get(entity_type_code) if entity_type_code else settings.ENTITY_MODELS_BY_CODE


def get_related_name_for_tag(dj_model):
    try:
        dj_field = dj_model._meta.get_field('tags')
    except FieldDoesNotExist:
        print(f'У django-модели {dj_model.__name__} должно быть поле "tags" для поддержки тегов')
        return

    return dj_field._related_name
