from django.conf import settings
from django.core.exceptions import FieldDoesNotExist


def get_dj_model(entity_type_code=None):  # TODO: rename to `get_gui_model`
    return settings.ENTITY_MODELS_BY_CODE.get(entity_type_code) if entity_type_code else settings.ENTITY_MODELS_BY_CODE


def register_gui(module, *gui_models):
    for gui_model_str in gui_models:
        gui_model = getattr(module, gui_model_str)
        settings.ENTITY_MODELS_BY_CODE[gui_model.dj_model.CODE] = gui_model


def get_related_name_for_tag(dj_model):
    try:
        dj_field = dj_model._meta.get_field('tags')
    except FieldDoesNotExist:
        print(f'У django-модели {dj_model.__name__} должно быть поле "tags" для поддержки тегов')
        return

    return dj_field._related_name
