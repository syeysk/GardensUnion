from django.urls import path
from gardensunion.base.views import (
    EntityTypesView,
    TagsView,
    EntitiesView,
    EntityView,
    EntityTagView,
    GetCreatingEntityFormView,
)

urlpatterns = [
    path('entity_type/', EntityTypesView.as_view(), name='entity_types'),
    path('tag/<int:type_entity_code>/', TagsView.as_view(), name='tags'),
    path('entity/<int:type_entity_code>/', EntitiesView.as_view(), name='enitities'),
    path('entity/<int:type_entity_code>/<int:entity_id>/', EntityView.as_view(), name='enitity'),
    path('entity/<int:type_entity_code>/creating_form/', GetCreatingEntityFormView.as_view(), name='get_data_to_create_enitity'),
    path('entity/<int:type_entity_code>/<int:entity_id>/tag/<int:tag_id>/', EntityTagView.as_view(), name='entity_tag'),
]
