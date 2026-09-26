from django.urls import path
from gardensunion.base.views import (
    EntityTypesView,
    TagsView,
    TagView,
    EntitiesView,
    EntityView,
    EntityTagView,
    GetCreatingEntityFormView,
    ActionsView,
)

urlpatterns = [
    path('type/', EntityTypesView.as_view(), name='entity_types'),
    path('type/<int:type_entity_code>/creating_form/', GetCreatingEntityFormView.as_view(), name='get_data_to_create_enitity'),
    path('type/<int:type_entity_code>/action/', ActionsView.as_view(), name='actions'),
    path('type/<int:type_entity_code>/tag/', TagsView.as_view(), name='tags'),
    path('type/<int:type_entity_code>/tag/<int:tag_id>/', TagView.as_view(), name='tag'),
    path('type/<int:type_entity_code>/entity/', EntitiesView.as_view(), name='enitities'),
    path('type/<int:type_entity_code>/entity/<int:entity_id>/', EntityView.as_view(), name='enitity'),
    path('type/<int:type_entity_code>/entity/<int:entity_id>/tag/<int:tag_id>/', EntityTagView.as_view(), name='entity_tag'),
]
