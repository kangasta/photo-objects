from django.urls import path

from . import views

app_name = "photos"
urlpatterns = [
    path("_auth", views.has_permission),
    path("albums", views.albums),
    path("albums/<str:album_key>/photos", views.photos),
]
