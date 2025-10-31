from datetime import datetime
import re
import unicodedata
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


def timestamp_str(timestamp: datetime):
    return timestamp.isoformat() if timestamp else None


def slugify(
        title: str | int,
        lower=False,
        replace_leading_underscores=False) -> str:
    key = unicodedata.normalize(
        'NFKD', str(title)).encode(
        'ascii', 'ignore').decode('ascii')
    if lower:
        key = key.lower()

    key = re.sub(r'[^a-zA-Z0-9._-]', '-', key)
    key = re.sub(r'[-_]{2,}', '-', key)

    if replace_leading_underscores:
        key = re.sub(r'^_+', '-', key)

    return key
