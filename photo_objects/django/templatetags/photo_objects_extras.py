from django import template


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
