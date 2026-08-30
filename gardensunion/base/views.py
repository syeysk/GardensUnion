from django.conf import settings
from django.core.exceptions import FieldDoesNotExist
from django.db.models import Q, Count, ForeignKey, BooleanField, IntegerField, TextField, NOT_PROVIDED
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from gardensunion.base.models import Tag
from gardensunion.base.serializers import EntityCreateSerializer, EntityUpdateSerializer

for gui_model_str in settings.ENTITY_TYPES:
    names_list = gui_model_str.split('.')
    package_list, gui_model_name = '.'.join(names_list[:-1]), names_list[-1]
    package = __import__(package_list, fromlist=[gui_model_name])
    gui_model = getattr(package, gui_model_name)
    settings.ENTITY_MODELS_BY_CODE[gui_model.dj_model.CODE] = gui_model


def get_tags(rows, dj_model, parent_id=None, deep=0):
    try:
        dj_field = dj_model._meta.get_field('tags')
    except FieldDoesNotExist:
        print(f'У django-модели {dj_model.__name__} должно быть поле "tags" для поддержки тегов')
        return

    related_name = dj_field._related_name
    for dj_tag in list(Tag.objects.filter(parent_id=parent_id, code=dj_model.CODE)):
        entities = getattr(dj_tag, related_name)
        rows.append({'count': entities.count(), 'name': dj_tag.name, 'id': dj_tag.pk, 'deep': deep})
        get_tags(rows, dj_model, dj_tag.pk, deep + 1)


def build_queryset_enitities(model, field_order, fields_search, tags=None, search=''):
    queryset = model.objects
    if search and fields_search:
        q_condition = None
        for field_search in fields_search:
            kwargs = {f'{field_search}__contains': search}
            q_part = Q(**kwargs)
            if q_condition is None:
                q_condition = q_part
            else:
                q_condition |= q_part

        queryset = queryset.filter(q_condition)
    
    if tags:
        queryset = queryset.filter(tags__pk__in=tags).annotate(Count('pk'))

    return queryset.order_by(field_order)


class EntityTypesView(APIView):
    def get(self, request):
        response_data = []
        for gui_model in settings.ENTITY_MODELS_BY_CODE.values():
            model = gui_model.dj_model
            response_data.append({'name_plural': model._meta.verbose_name_plural, 'name': model._meta.verbose_name, 'code': model.CODE})

        return Response(status=status.HTTP_200_OK, data=response_data)


class TagsView(APIView):
    def get(self, request, type_entity_code):
        response_data = []
        gui_model = settings.ENTITY_MODELS_BY_CODE[type_entity_code]
        get_tags(response_data, gui_model.dj_model)
        return Response(status=status.HTTP_200_OK, data=response_data)


class EntitiesView(APIView):
    def post(self, request, type_entity_code):
        tags_id = None
        search_text = ''

        headers = []
        entites = []
        count_total = 0
        gui_model = settings.ENTITY_MODELS_BY_CODE.get(type_entity_code)
        if gui_model:
            queryset = build_queryset_enitities(
                gui_model.dj_model,
                getattr(gui_model, 'field_order', 'pk'),
                getattr(gui_model, 'field_search', []),
                tags_id,
                search_text,
            )
            count_total = queryset.count()
            table_fields = getattr(gui_model, 'table_fields', [])
            for entity in queryset:
                entites.append({'id': entity.pk, 'row': tuple(str(getattr(entity, field_name)) for field_name in table_fields)})

        response_data = {'entites': entites, 'headers': headers, 'count_total': count_total}
        return Response(status=status.HTTP_200_OK, data=response_data)

    def put(self, request, type_entity_code):
        gui_model = settings.ENTITY_MODELS_BY_CODE.get(type_entity_code)
        # TODO: Если не сущестует модели, то отдавать ошибку с текстом "Сущность с таким ID не существует"
        serializer = EntityCreateSerializer(gui_model.dj_model, gui_model.table_fields, data=request.data)
        serializer.is_valid(raise_exception=True)
        entity = serializer.save()
        return Response(status=status.HTTP_200_OK, data={'id': entity.id})


class EntityView(APIView):
    def get(self, request, type_entity_code, entity_id):
        fields = []
        gui_model = settings.ENTITY_MODELS_BY_CODE.get(type_entity_code)
        if gui_model:
            dj_model = gui_model.dj_model
            entity = dj_model.objects.filter(pk=entity_id).first()
            response_data = {
                'window': getattr(gui_model,'window_name', 'default'),
                'fields': fields,
                'title': dj_model._meta.verbose_name,
            }
            for field_name in getattr(gui_model, 'window_fields', ['id']):
                dj_field = dj_model._meta.get_field(field_name)
                choices = dj_field.choices
                value = getattr(entity, field_name)
                if isinstance(dj_field, ForeignKey):
                    value = [value.pk if value else None, str(value)]
                fields.append(
                    {
                        'title': dj_field.verbose_name.capitalize(),
                        'name': field_name,
                        'value': value,
                        'type': '',
                    }
                )
        else:  # TODO: Удалить, отдавать 404 или типа того
            response_data = {'window': 'default', 'fields': fields}

        return Response(status=status.HTTP_200_OK, data=response_data)

    def post(self, request, type_entity_code, entity_id):
        gui_model = settings.ENTITY_MODELS_BY_CODE.get(type_entity_code)
        entity = gui_model.dj_model.objects.filter(id=entity_id).first()
        response_data = {}
        serializer = EntityUpdateSerializer(gui_model.dj_model, gui_model.table_fields, entity, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        response_data['updated_fields'] = [
            name for name, value in serializer.validated_data.items() if getattr(entity, name) != value
        ]
        serializer.save()

        return Response(status=status.HTTP_200_OK, data=response_data)


class GetCreatingEntityFormView(APIView):
    def get(self, request, type_entity_code):
        fields = []
        gui_model = settings.ENTITY_MODELS_BY_CODE.get(type_entity_code)
        dj_model = gui_model.dj_model
        if gui_model:
            response_data = {
                'window': getattr(gui_model,'window_name', 'default'),
                'fields': fields,
                'title': dj_model._meta.verbose_name,
            }
            for field_name in getattr(gui_model, 'window_fields', ['id']):
                dj_field = dj_model._meta.get_field(field_name)
                choices = dj_field.choices
                default_value = ''
                if isinstance(dj_field, ForeignKey):
                    default_value = [1, '']
                fields.append(
                    {
                        'title': dj_field.verbose_name.capitalize(),
                        'name': field_name,
                        'value': default_value,
                        'type': '',
                    }
                )
        else:  # TODO: Удалить, отдавать 404 или типа того
            response_data = {'window': 'default', 'fields': fields}

        return Response(status=status.HTTP_200_OK, data=response_data)
