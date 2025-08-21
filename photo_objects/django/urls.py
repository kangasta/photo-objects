from django.contrib.auth import views as auth_views
from django.http import HttpResponseRedirect
from django.urls import path

from .views import api, ui

app_name = "photo_objects"
urlpatterns = [
    path("_auth", api.has_permission),
    path("api/albums", api.albums),
    path("api/albums/<str:album_key>", api.album),
    path("api/albums/<str:album_key>/photos", api.photos),
    path("api/albums/<str:album_key>/photos/<str:photo_key>", api.photo),
    path("api/albums/<str:album_key>/photos/<str:photo_key>/img", api.get_img),
    # TODO: ui views
    path('', lambda _: HttpResponseRedirect('albums')),
    path(
        "albums",
        ui.list_albums,
        name="list_albums",
    ),
    path(
        "albums/_new",
        ui.new_album,
        name="new_album",
    ),
    path(
        "albums/<str:album_key>",
        ui.show_album,
        name="show_album",
    ),
    path(
        "albums/<str:album_key>/_edit",
        ui.edit_album,
        name="edit_album",
    ),
    path(
        "albums/<str:album_key>/_delete",
        ui.delete_album,
        name="delete_album",
    ),
    path(
        "albums/<str:album_key>/photos/_upload",
        ui.upload_photos,
        name="upload_photos",
    ),
    path(
        "albums/<str:album_key>/photos/<str:photo_key>",
        ui.show_photo,
        name="show_photo",
    ),
    path(
        "albums/<str:album_key>/photos/<str:photo_key>/_edit",
        ui.edit_photo,
        name="edit_photo",
    ),
    path(
        "albums/<str:album_key>/photos/<str:photo_key>/_delete",
        ui.delete_photo,
        name="delete_photo",
    ),
    path(
        "configuration",
        ui.configuration,
        name="configuration",
    ),
    # TODO: img/<str:album_key>/<str:photo_key>/<str:size_key> path
    path(
        "users/login",
        ui.login,
        name="login",
    ),
    path(
        "users/logout",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),
]
