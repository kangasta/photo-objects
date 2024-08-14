from django.urls import path

from . import views

app_name = "photos"
urlpatterns = [
    path("_auth", views.has_permission),
    path("api/albums", views.albums),
    path("api/albums/<str:album_key>", views.album),
    path("api/albums/<str:album_key>/photos", views.photos),
    path("api/albums/<str:album_key>/photos/<str:photo_key>", views.photo),
    path(
        "api/albums/<str:album_key>/photos/<str:photo_key>/img",
        views.get_img,
    ),
    # TODO: img/<str:album_key>/<str:photo_key>/<str:size_key> path
    # TODO: ui views
]
