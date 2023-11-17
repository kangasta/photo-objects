from django.urls import path

from . import views

urlpatterns = [
    path("_auth", views.has_permission),
    path("albums", views.get_albums),
]
