from xml.etree import ElementTree as ET

from django.http import HttpRequest
from django.utils.dateformat import format as format_date
from django.utils.safestring import mark_safe
from markdown import markdown

from photo_objects.django.models import Album, Photo


class BackLink:
    def __init__(self, text, url):
        self.text = text
        self.url = url


def render_markdown(value):
    return mark_safe(markdown(value))


def _first_paragraph_textcontent(raw) -> str | None:
    html = render_markdown(raw)
    root = ET.fromstring(f"<root>{html}</root>")

    first = root.find("p")
    if first is None:
        return None

    return ''.join(first.itertext())


def _default_album_description(request: HttpRequest, album: Album) -> str:
    count = album.photo_set.count()
    plural = 's' if count != 1 else ''
    return f"Album with {count} photo{plural} in {request.site.name}."


def _default_photo_description(photo: Photo) -> str:
    date_str = format_date(photo.timestamp, "F Y")
    return f"Photo from {date_str} in {photo.album.title} album."


def meta_description(
        request: HttpRequest,
        resource: Album | Photo | str | None) -> str:
    text = None
    if isinstance(resource, Album):
        text = (
            _first_paragraph_textcontent(resource.description) or
            _default_album_description(request, resource))

    if isinstance(resource, Photo):
        text = (
            _first_paragraph_textcontent(resource.description) or
            _default_photo_description(resource))

    if isinstance(resource, str):
        text = _first_paragraph_textcontent(resource)

    return text or "A simple self-hosted photo server."
