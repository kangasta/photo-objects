from django.contrib.auth import views as auth_views
from django.http import HttpRequest
from django.urls import reverse_lazy

from photo_objects.django.api.album import get_site_album
from photo_objects.django.views.utils import BackLink


def login(request: HttpRequest):
    album, _ = get_site_album(request.site)

    return auth_views.LoginView.as_view(
        template_name="photo_objects/form.html",
        extra_context={
            "title": "Login",
            "photo": album.cover_photo,
            "action": "Login",
            "back": BackLink(
                f'Back to albums',
                reverse_lazy('photo_objects:list_albums')),
            "class": "login"
        },
    )(request)
