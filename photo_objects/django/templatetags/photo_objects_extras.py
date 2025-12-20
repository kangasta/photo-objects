from datetime import datetime
from django import template
from django.utils.safestring import mark_safe
from django.utils.html import escape

from photo_objects.django.models import SiteSettings
from photo_objects.django.views.utils import meta_description


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

        settings = SiteSettings.objects.get(site)

        return {
            'request': request,
            "title": site.name,
            "description": meta_description(request, settings.description),
            "photo": settings.preview_image,
        }
    except Exception:
        return context


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
