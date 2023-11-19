from django.urls import path

from . import views

app_name = "photos"
urlpatterns = [
    path("_auth", views.has_permission),
    path("albums", views.get_albums),
    path("photos/pending", views.get_pending_photos),
]
