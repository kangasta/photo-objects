from dataclasses import dataclass

from django.http import HttpRequest
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from photo_objects.django.api.utils import JsonProblem
from photo_objects.django.views.utils import BackLink
from photo_objects.utils import render_markdown

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


def site_preview_configured(request: HttpRequest) -> Validation:
    detail = None

    ok = request.site.settings.preview_image is not None
    if ok:
        detail = (
            f'The site settings for `{request.site.domain}` configure a '
            'preview image.'
        )
    else:
        detail = (
            'Configure a preview image in site settings for '
            f'`{request.site.domain}`.'
        )

    return Validation(
        check=_("Site has a default preview image"),
        status=status(ok),
        detail=detail,
    )


def site_description_configured(request: HttpRequest) -> Validation:
    detail = None

    settings = request.site.settings
    ok = settings.description is not None and len(settings.description) > 0
    if ok:
        detail = (
            f'The site settings for `{request.site.domain}` configure a '
            'description.'
        )
    else:
        detail = (
            'Configure a description in site settings for '
            f'`{request.site.domain}`.'
        )

    return Validation(
        check=_("Site has a default description"),
        status=status(ok),
        detail=detail,
    )


@json_problem_as_html
def configuration(request: HttpRequest):
    if not request.user.is_staff:
        raise JsonProblem("Page not found", status=404)

    validations = [
        uses_https(request),
        site_is_configured(request),
        domain_matches_request(request),
        site_preview_configured(request),
        site_description_configured(request),
    ]

    back = BackLink("Back to albums", reverse('photo_objects:list_albums'))

    return render(request, "photo_objects/configuration.html", {
        "title": "Configuration",
        "validations": validations,
        "back": back,
    })
