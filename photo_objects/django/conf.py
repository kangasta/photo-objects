from dataclasses import dataclass
from enum import Enum

from django.conf import settings

from photo_objects.utils import pretty_list


def objsto_settings() -> dict:
    return settings.PHOTO_OBJECTS_OBJSTO


class PhotoSize(Enum):
    TINY = "xs"
    SMALL = "sm"
    MEDIUM = "md"
    LARGE = "lg"
    ORIGINAL = "og"


CONFIGURABLE_PHOTO_SIZES = [
    PhotoSize.SMALL.value,
    PhotoSize.MEDIUM.value,
    PhotoSize.LARGE.value
]


@dataclass()
class PhotoSizeDimensions:
    max_width: int = None
    max_height: int = None
    max_aspect_ratio: float = None
    image_format: str = None


DEFAULT_SM = dict(
    max_width=512,
    max_height=512,
    max_aspect_ratio=1.5,
    image_format='WEBP'
)
DEFAULT_MD = dict(
    max_width=1024,
    max_height=1024,
    max_aspect_ratio=1.5,
    image_format="JPEG"
)
DEFAULT_LG = dict(
    max_width=2048,
    max_height=2048,
    image_format='WEBP'
)


@dataclass
class PhotoSizes:
    version: int = None
    sm: PhotoSizeDimensions = None
    md: PhotoSizeDimensions = None
    lg: PhotoSizeDimensions = None


def validate_photo_sizes(data: dict, prefix=None) -> list[str]:
    prefix = prefix or "Photo size"
    errors = []

    for key, value in data.items():
        allowed_keys = CONFIGURABLE_PHOTO_SIZES + ["version"]
        if key not in allowed_keys:
            expected = pretty_list(allowed_keys, 'or')
            errors.append(
                f"{prefix} key '{key}' is invalid, expected one of {expected}")

        if key == "version":
            continue

        if not isinstance(value, dict):
            errors.append(f"{prefix} '{key}' must be a dict.")

        if 'max_width' not in value and 'max_height' not in value:
            errors.append(
                f"{prefix} '{key}' must define at least one dimension.")

        if (
            'max_aspect_ratio' in value and
            value['max_aspect_ratio'] is not None and
            not isinstance(value['max_aspect_ratio'], (float, int))
        ):
            errors.append(
                f"{prefix} '{key}' max_aspect_ratio must be a number.")

    return errors


def parse_photo_sizes(data: dict) -> PhotoSizes:
    errors = validate_photo_sizes(data)

    if errors:
        raise ValueError(
            f"Invalid photo sizes configuration: {' '.join(errors)}")

    return PhotoSizes(
        version=data.get('version'),
        sm=PhotoSizeDimensions(**data.get('sm', DEFAULT_SM)),
        md=PhotoSizeDimensions(**data.get('md', DEFAULT_MD)),
        lg=PhotoSizeDimensions(**data.get('lg', DEFAULT_LG)),
    )


def photo_sizes() -> PhotoSizes:
    try:
        data = settings.PHOTO_OBJECTS_PHOTO_SIZES
    except AttributeError:
        data = {}

    data = {**data, "version": 1}
    return parse_photo_sizes(data)
