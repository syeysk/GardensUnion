from django.db.models import Q, Count, ForeignKey, IntegerField, CharField, DateTimeField
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from gardensunion.base.utils import get_dj_model
from gardensunion.link.models import Link
from gardensunion.link.serializers import LinkSerializer


def build_queryset_enitities(model, field_order, fields_search, search=''):
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

    return queryset.order_by(field_order)


class LinksView(APIView):
    '''Отдаёт ответ аналогично base.views.EntitiesView'''
    def post(self, request):
        main_id = request.data.get('main_id', 0)
        main_code = request.data.get('main_code', 0)
        cur_page = request.data.get('p', 0)
        count_on_page = 30

        links = []
        gui_model = get_dj_model(main_code)
        if not gui_model:
            return Response(status=status.HTTP_200_OK, data={'message': 'Не найдена модель'})

        queryset = build_queryset_enitities(
            Link,
            'pk',
            [],
            '',
        )
        queryset = queryset.filter(Q(**{'left_code': main_code, 'left_id': main_id}) | Q(**{'right_code': main_code, 'right_id': main_id}))
        count_total = queryset.count()
        count_pages = (count_total // count_on_page) + (1 if count_total % count_on_page else 0)
        cur_page = cur_page if 0 <= cur_page < count_pages else 0
        for link in list(queryset[cur_page * count_on_page:(cur_page * count_on_page) + count_on_page]):
            if link.left_code == main_code and link.left_id == main_id:
                slave_code = link.right_code
                slave_id = link.right_id
            else:
                slave_code = link.left_code
                slave_id = link.left_id

            dj_model = get_dj_model(slave_code).dj_model
            slave_entity = dj_model.objects.filter(pk=slave_id).first()
            row = [dj_model._meta.verbose_name, str(slave_entity)]
            links.append({'id': link.pk, 'row': row, 'tags': {}})

        response_data = {
            'entites': links,
            'headers': [],
            'count_entites_total': count_total,
            'cur_page': cur_page,
            'count_pages': count_pages,
            'prev_page': cur_page - 1 if cur_page > 0 else count_pages - 1,
            'next_page': cur_page + 1 if cur_page < count_pages else 0,
            'table_name': 'default', #getattr(gui_model, 'table_name', 'default'),
        }
        return Response(status=status.HTTP_200_OK, data=response_data)

    def put(self, request):
        serializer = LinkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)  # TODO: Проверить в сериализаторе, что нет таких комбинаций в обоих навравлениях (left-right, right-left)
        link = serializer.save()
        return Response(status=status.HTTP_200_OK, data={'id': link.id})


class LinkView(APIView):
    def get(self, request, link_id):
        ''' Отдаёт ответ аналогично base.views.EntityView '''
        link = Link.objects.filter(pk=link_id).first()
        dj_model_left = get_dj_model(link.left_code).dj_model
        left_entity = dj_model_left.objects.filter(pk=link.left_id).first()
        dj_model_right = get_dj_model(link.right_code).dj_model
        right_entity = dj_model_right.objects.filter(pk=link.right_id).first()
        fields = {
            'left': {
                'title': dj_model_left._meta.verbose_name,
                'name': 'left',
                'value': link.left_id,
                'type': 'Foreign',
                'value_str': str(left_entity),
                'entity_type_code': link.left_code,
            },
            'right': {
                'title': dj_model_right._meta.verbose_name,
                'name': 'right',
                'value': link.right_id,
                'type': 'Foreign',
                'value_str': str(right_entity),
                'entity_type_code': link.right_code,
            },
        }
        response_data = {
            'window': 'default',
            'fields': fields,
            'title': 'Связь',
        }
        return Response(status=status.HTTP_200_OK, data=response_data)

    def post(self, request, link_id):
        ''' Отдаёт ответ аналогично base.views.EntityView '''
        link = Link.objects.filter(pk=link_id).first()
        serializer = LinkSerializer(link, data=request.data)
        serializer.is_valid(raise_exception=True)
        response_data = {
            'updated_fields': [
                name[:-3] for name, value in serializer.validated_data.items() if getattr(link, name) != value
            ]
        }
        link = serializer.save()
        return Response(status=status.HTTP_200_OK, data=response_data)

    def delete(self, request, link_id):
        ''' Отдаёт ответ аналогично base.views.EntityView '''
        link = Link.objects.filter(pk=link_id)
        link.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class GetCreatingLinkFormView(APIView):
    def get(self, request):
        ''' Отдаёт ответ аналогично base.views.GetCreatingEntityFormView '''
        main_id = int(request.query_params.get('main_id', '0'))
        main_code = int(request.query_params.get('main_code', '0'))
        slave_code = int(request.query_params.get('slave_code', '0'))
        gui_model = get_dj_model(main_code)
        if not gui_model:
            response_data = {'window': 'default', 'fields': {}}

        slave_model = get_dj_model(slave_code).dj_model
        main_model = gui_model.dj_model
        main_entity = main_model.objects.filter(pk=main_id).first()

        fields = {
            'left': {
                'title': main_model._meta.verbose_name,
                'name': 'left',
                'value': main_id,
                'type': 'Foreign',
                'value_str': str(main_entity),
                'entity_type_code': main_code,
            },
            'right': {
                'title': slave_model._meta.verbose_name,
                'name': 'right',
                'value': None,
                'type': 'Foreign',
                'value_str': '',
                'entity_type_code': slave_code,
            },
        }
        response_data = {
            'window': getattr(gui_model,'window_name', 'default'),
            'fields': fields,
            'title': 'Связь',
        }
        return Response(status=status.HTTP_200_OK, data=response_data)
