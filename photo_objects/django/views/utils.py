from django.http import HttpRequest
from django.utils.dateformat import format as format_date

from photo_objects.django.models import Album, Photo, SiteSettings
from photo_objects.utils import first_paragraph_textcontent


class BackLink:
    def __init__(self, text: str, url: str):
        self.text = text
        self.url = url


# TODO: Use this also for meta-og tags
class Preview:
    def __init__(
            self,
            request: HttpRequest,
            resource: Album | Photo = None,
            helptext: str = None):
        self.description = meta_description(request, resource)
        self.photo = meta_photo(request, resource)
        self.title = meta_title(request, resource)
        self.helptext = helptext


def _default_album_description(request: HttpRequest, album: Album) -> str:
    count = album.photo_set.count()
    plural = 's' if count != 1 else ''
    return f"Album with {count} photo{plural} in {request.site.name}."


def _default_photo_description(photo: Photo) -> str:
    date_str = format_date(photo.timestamp, "F Y")
    return f"Photo from {date_str} in {photo.album.title} album."


def meta_description(
        request: HttpRequest,
        resource: Album | Photo | str = None) -> str:
    text = None
    if isinstance(resource, Album):
        return (
            first_paragraph_textcontent(resource.description) or
            _default_album_description(request, resource))

    if isinstance(resource, Photo):
        return (
            first_paragraph_textcontent(resource.description) or
            _default_photo_description(resource))

    if isinstance(resource, str):
        return first_paragraph_textcontent(resource)

    settings = SiteSettings.objects.get(request.site)
    text = first_paragraph_textcontent(settings.description)
    return text or "A simple self-hosted photo server."


def meta_photo(
        request: HttpRequest,
        resource: Album | Photo = None) -> Photo:
    if isinstance(resource, Photo):
        return resource

    if isinstance(resource, Album):
        return resource.cover_photo

    settings = SiteSettings.objects.get(request.site)
    return settings.preview_image


def meta_title(
        request: HttpRequest,
        resource: Album | Photo | str = None) -> str:
    text = None
    if isinstance(resource, Album):
        text = resource.title

    if isinstance(resource, Photo):
        text = resource.title or resource.filename

    if isinstance(resource, str):
        text = resource

    return text or request.site.name
