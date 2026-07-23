from django.contrib.auth import views as auth_views
from django.http import HttpRequest

from photo_objects.django.views.utils import Preview


def login(request: HttpRequest):
    return auth_views.LoginView.as_view(
        template_name="photo_objects/form.html",
        extra_context={
            "title": "Login",
            "action": "Login",
            "class": "login",
            "width": "narrow",
            "preview": Preview(request, None),
        },
    )(request)
