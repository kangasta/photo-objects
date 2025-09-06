from xml.etree import ElementTree as ET

from django.utils.safestring import mark_safe
from markdown import markdown


def pretty_list(in_: list, conjunction: str):
    return f' {conjunction} '.join(
        i for i in (', '.join(in_[:-1]), in_[-1],) if i)


def render_markdown(value: str):
    return mark_safe(markdown(value))


def first_paragraph_textcontent(raw: str) -> str | None:
    html = render_markdown(raw)
    root = ET.fromstring(f"<root>{html}</root>")

    first = root.find("p")
    if first is None:
        return None

    return ''.join(first.itertext())
