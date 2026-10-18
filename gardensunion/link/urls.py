from django.urls import path
from gardensunion.link.views import (
    LinksView,
    LinkView,
    GetCreatingLinkFormView,
)

urlpatterns = [
    path('', LinksView.as_view(), name='links'),
    path('<int:link_id>/', LinkView.as_view(), name='link'),
    path('creating_form/', GetCreatingLinkFormView.as_view(), name='link_creating_form'),
]
