from datetime import datetime
from django import template

from photo_objects.django.api.album import get_site_album


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
def is_datetime(value):
    return isinstance(value, datetime)


@register.filter
def is_list(value):
    return isinstance(value, list)


@register.inclusion_tag("photo_objects/meta-og.html", takes_context=True)
def meta_og(context):
    photo = context.get("photo")
    title = context.get("title")

    if photo and title:
        return context

    try:
        request = context.get("request")
        site = request.site
        album = get_site_album(site.id)

        return {
            'request': request,
            "title": album.title or site.name,
            "description": album.description,
            "photo": album.cover_photo,
        }
    except Exception:
        return context
