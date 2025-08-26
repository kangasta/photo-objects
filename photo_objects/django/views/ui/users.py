from django.contrib.auth import views as auth_views
from django.http import HttpRequest
from django.urls import reverse_lazy

from photo_objects.django.models import SiteSettings
from photo_objects.django.views.utils import BackLink


def login(request: HttpRequest):
    settings = SiteSettings.objects.get(request.site)

    return auth_views.LoginView.as_view(
        template_name="photo_objects/form.html",
        extra_context={
            "title": "Login",
            "photo": settings.preview_image,
            "action": "Login",
            "back": BackLink(
                'Back to albums',
                reverse_lazy('photo_objects:list_albums')),
            "class": "login"
        },
    )(request)
