from django.utils.safestring import mark_safe
from markdown import markdown


class BackLink:
    def __init__(self, text, url):
        self.text = text
        self.url = url


def render_markdown(value):
    return mark_safe(markdown(value))
