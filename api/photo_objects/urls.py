from django.urls import path

from . import views

app_name = "photos"
urlpatterns = [
    path("_auth", views.has_permission),
    path("albums", views.albums),
    path("albums/<str:album_key>/photos", views.photos),
    path("albums/<str:album_key>/photos/<str:photo_key>", views.photo),
    path("albums/<str:album_key>/photos/<str:photo_key>/img", views.get_img),
]
