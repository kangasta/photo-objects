from datetime import datetime

from django import template
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.html import escape

from photo_objects.django.models import (
    Album,
    Photo,
    PhotoReference,
    SiteSettings,
    Story,
)
from photo_objects.django.views.utils import (
    PreviewLink,
    PreviewLinks,
    TagLinks,
    meta_description,
)


register = template.Library()


@register.filter
def initials(user):
    initials = ''
    if user.first_name:
        initials += user.first_name[0]
    if user.last_name:
        initials += user.last_name[0]
    if not initials:
        initials = user.username[0]
    return initials.upper()


@register.filter
def display_name(user):
    if user.first_name or user.last_name:
        return f'{user.first_name} {user.last_name}'.strip()
    return user.username


@register.filter
def first_key(d: dict):
    return next(iter(d.keys()), None)


@register.filter
def is_datetime(value):
    return isinstance(value, datetime)


@register.filter
def is_list(value):
    return isinstance(value, list)


@register.filter
def is_preview_link(value):
    return isinstance(value, PreviewLink)


@register.filter
def is_preview_links(value):
    return isinstance(value, PreviewLinks)


@register.filter
def is_reference(value):
    return isinstance(value, PhotoReference)


@register.filter
def is_tag_links(value):
    return isinstance(value, TagLinks)


@register.inclusion_tag("photo_objects/inclusion_tag/meta-og.html",
                        takes_context=True)
def meta_og(context):
    photo = context.get("photo")
    title = context.get("title")

    if isinstance(photo, PhotoReference):
        photo = photo.photo

    if photo and title:
        return {
            **context.flatten(),
            "photo": photo,
        }

    try:
        request = context.get("request")
        site = request.site

        settings = SiteSettings.objects.get(site)

        return {
            "request": request,
            "title": site.name,
            "description": meta_description(request, settings.description),
            "photo": settings.preview_image,
        }
    except Exception:
        return context


def _photo_context(photo: Photo, size: str, thumbnail: bool = False):
    if not photo:
        return {}

    return {
        "photo": photo,
        "size": size,
        "height": photo.thumbnail_height if thumbnail else photo.height,
        "width": photo.thumbnail_width if thumbnail else photo.width,
    }


@register.inclusion_tag(
    "photo_objects/inclusion_tag/photo-img.html",
    takes_context=True)
def site_preview_img(context):
    try:
        request = context.get("request")
        site = request.site

        settings = SiteSettings.objects.get(site)

        return _photo_context(settings.preview_image, "sm", thumbnail=True)
    except Exception:
        return context


@register.inclusion_tag(
    "photo_objects/inclusion_tag/preview-link.html")
def preview_link(link: PreviewLink):
    return {
        "link": link,
    }


@register.inclusion_tag(
    "photo_objects/inclusion_tag/photo-img.html")
def photo_img(
        photo: Photo | PhotoReference,
        size: str,
        thumbnail: bool = False):
    if isinstance(photo, PhotoReference):
        photo = photo.photo

    return _photo_context(photo, size, thumbnail)


@register.inclusion_tag(
    "photo_objects/inclusion_tag/photo-link.html")
def photo_link(
        photo: Photo | PhotoReference,
        collection: Album | Story = None,
        **kwargs):
    title = photo.title
    if isinstance(photo, PhotoReference):
        photo = photo.photo
    if not title:
        title = photo.filename

    if isinstance(collection, Album):
        href = reverse(
            'photo_objects:show_album_photo',
            kwargs={
                "album_key": collection.key,
                "photo_key": photo.filename})
    elif isinstance(collection, Story):
        href = reverse(
            'photo_objects:show_story_photo',
            kwargs={
                "story_key": collection.key,
                "photo_uuid": photo.uuid})
    else:
        href = reverse(
            'photo_objects:show_photo',
            kwargs={"photo_uuid": photo.uuid})

    return {
        "photo": photo,
        "title": title,
        "href": href,
        "class": kwargs.get("class", ""),
    }


@register.simple_tag(takes_context=True)
def copyright_notice(context):
    try:
        request = context.get("request")
        site = request.site

        settings = SiteSettings.objects.get(site)

        if settings.copyright_notice:
            notice = escape(settings.copyright_notice)
            return mark_safe(f"<div>{notice}</div>")
        return ""
    except Exception:
        return ""
