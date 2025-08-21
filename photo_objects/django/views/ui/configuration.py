from dataclasses import dataclass

from django.http import HttpRequest
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from photo_objects.django.models import Album
from photo_objects.django.views.utils import BackLink, render_markdown

from .utils import json_problem_as_html


@dataclass
class Validation:
    check: str
    status: str
    detail: str = None

    def __post_init__(self):
        self.detail = render_markdown(self.detail)


def status(ok: bool, warning=False) -> str:
    if ok:
        return _("OK")
    if warning:
        return _("Warning")
    return _("Error")


def uses_https(request: HttpRequest) -> Validation:
    ok = request.is_secure()
    warning = False
    detail = (
        'The request received by the API server was '
        f'{"" if ok else "not "}secure.')

    if not ok:
        referer = request.META.get("HTTP_REFERER", "")
        if request.site.domain in referer and referer.startswith("https://"):
            warning = True

            detail += _(
                ' If you are running the API server behind a reverse proxy or '
                'a load-balancer, ensure that HTTPS termination is configured '
                'correctly.')

    return Validation(
        check=_("Site is served over HTTPS"),
        status=status(ok, warning),
        detail=detail
    )


def site_is_configured(request: HttpRequest) -> Validation:
    detail = (
        'Site domain is configured to a non-default value: '
        f'`{request.site.domain}`'
    )
    try:
        ok = request.site.domain != "example.com"
        if not ok:
            detail = (
                'Site domain is set to `example.com`. This is a placeholder '
                'domain and should be changed to the actual domain of the '
                'site.')
    except Exception as e:
        ok = False
        detail = (
            f"Failed to resolve site domain: got `{str(e)}`. Check that sites "
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
                'Host in the request does not match domain configured for '
                f'the site: expected `{domain}`, got `{host}`.')
        else:
            detail = (
                f'Host in the request, `{host}`, matches domain configured '
                f'for the site, `{domain}`.'
            )
    except Exception as e:
        ok = False
        detail = (
            f"Failed to resolve host or domain: got `{str(e)}`. Check that "
            "sites framework is installed, site middleware is configured, "
            "and that the site exists in the database.")

    return Validation(
        check=_("Configured domain matches host in request"),
        status=status(ok),
        detail=detail,
    )


def site_preview_configured(
        request: HttpRequest,
        album: Album | Exception) -> Validation:
    detail = None

    if isinstance(album, Exception):
        ok = False
        detail = f'Failed to resolve site or album: `{str(album)}`'
    else:
        ok = album.cover_photo is not None
        if ok:
            detail = (
                f'The `{album.key}` album has a cover photo configured. This '
                'photo will be used as the site preview image.'
            )
        else:
            detail = (
                f'Set cover photo for `{album.key}` album to configure '
                'the preview image.')

    return Validation(
        check=_("Site has a default preview image"),
        status=status(ok),
        detail=detail,
    )


def site_description_configured(
        request: HttpRequest,
        album: Album | Exception) -> Validation:
    detail = None

    if isinstance(album, Exception):
        ok = False
        detail = f'Failed to resolve site or album: `{str(album)}`'
    else:
        ok = album.description is not None and len(album.description) > 0
        if ok:
            detail = (
                f'The `{album.key}` album has a description. This description '
                'will be used as the site description.'
            )
        else:
            detail = (
                f'Set description for `{album.key}` album to configure '
                'the site description.')

    return Validation(
        check=_("Site has a default description"),
        status=status(ok),
        detail=detail,
    )


@json_problem_as_html
def configuration(request: HttpRequest):
    try:
        site_id = request.site.id
        album_key = f"_site_{site_id}"
        album = Album.objects.get(key=album_key)
    except Exception as e:
        album = e

    validations = [
        uses_https(request),
        site_is_configured(request),
        domain_matches_request(request),
        site_preview_configured(request, album),
        site_description_configured(request, album),
    ]

    back = BackLink("Back to albums", reverse('photo_objects:list_albums'))

    return render(request, "photo_objects/configuration.html", {
        "title": "Configuration",
        "validations": validations,
        "back": back,
    })
