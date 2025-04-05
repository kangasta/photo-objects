from dataclasses import dataclass

from django.http import HttpRequest
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from photo_objects.django.models import Album
from photo_objects.django.views.utils import BackLink

from .utils import json_problem_as_html


@dataclass
class Validation:
    check: str
    status: str
    detail: str = None


def status(b: bool) -> str:
    return _("OK") if b else _("Error")


def uses_https(request: HttpRequest) -> Validation:
    return Validation(
        check=_("Site is served over HTTPS"),
        status=status(request.is_secure()),
    )


def site_is_configured(request: HttpRequest) -> Validation:
    detail = None
    try:
        ok = request.site.domain != "example.com"
        if not ok:
            detail = (
                f'Site domain is set to "example.com". This is a placeholder '
                'domain and should be changed to the actual domain of the '
                'site.')
    except Exception as e:
        ok = False
        detail = (
            f"Failed to resolve site domain: {str(e)}. Check that sites "
            "framework is installed, site middleware is configured, and that "
            "the site exists in the database.")

    return Validation(
        check=_("Site is configured"),
        status=status(ok),
        detail=detail,
    )


def domain_matches_request(request: HttpRequest) -> Validation:
    detail = None
    try:
        host = request.get_host().lower()
        domain = request.site.domain.lower()
        ok = request.get_host() == request.site.domain
        if not ok:
            detail = (
                f'Host in the request does not match domain configured for '
                'the site: expected "{domain}", got "{host}".')
    except Exception as e:
        ok = False
        detail = (
            f"Failed to resolve host or domain: {str(e)}. Check that "
            "sites framework is installed, site middleware is configured, "
            "and that the site exists in the database.")

    return Validation(
        check=_("Configured domain matches host in request"),
        status=status(ok),
        detail=detail,
    )


def site_preview_configured(request: HttpRequest) -> Validation:
    detail = None

    try:
        site_id = request.site.id
        album_key = f"_site_{site_id}"
        album = Album.objects.get(key=album_key)
        ok = album.cover_photo is not None
        if not ok:
            detail = (
                f'Set cover photo for "{album_key}" album to configure '
                'the preview image.')
    except Exception as e:
        ok = False
        detail = f'Failed to resolve site or album: {str(e)}'

    return Validation(
        check=_("Site has a default preview image"),
        status=status(ok),
        detail=detail,
    )


@json_problem_as_html
def configuration(request: HttpRequest):
    validations = [
        uses_https(request),
        site_is_configured(request),
        domain_matches_request(request),
        site_preview_configured(request),
    ]

    back = BackLink("Back to albums", reverse('photo_objects:list_albums'))

    return render(request, "photo_objects/configuration.html", {
        "title": "Configuration",
        "validations": validations,
        "back": back,
    })
