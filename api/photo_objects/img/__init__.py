from base64 import b64encode
from datetime import datetime
from io import BytesIO

from PIL import Image, ExifTags

from photo_objects.error import PhotoObjectsError

from ._utils import utcnow


def _read_original_datetime(image: Image) -> datetime:
    try:
        for key, value in ExifTags.TAGS.items():
            if value == "ExifOffset":
                break

        info = image.getexif().get_ifd(key)

        time = info.get(ExifTags.Base.DateTimeOriginal)
        subsec = info.get(ExifTags.Base.SubsecTimeOriginal) or "0"
        offset = info.get(ExifTags.Base.OffsetTimeOriginal) or "+00:00"

        return datetime.strptime(
            f"{time}.{subsec}{offset}",
            "%Y:%m:%d %H:%M:%S.%f%z")
    except BaseException:
        return None


def _image_format(filename):
    image_format = filename.split('.')[-1].upper()

    if image_format == "JPG":
        return "JPEG"

    return image_format


def photo_details(photo_file):
    image = Image.open(photo_file)

    width, height = image.size
    timestamp = _read_original_datetime(image) or utcnow()

    # TODO: remove all extra data from the image
    resized = image.resize((3, 3))

    b = BytesIO()
    resized.save(b, format='PNG', optimize=True, icc_profile=None)

    return dict(
        timestamp=timestamp,
        width=width,
        height=height,
        tiny_base64=b64encode(b.getvalue()).decode('ascii')
    )


def scale_photo(photo_file, filename, max_width=None, max_height=None):
    image = Image.open(photo_file)
    width, height = image.size

    if max_width and max_height:
        ratio = min(
            max_width / width,
            max_height / height
        )
    elif max_width:
        ratio = max_width / width
    elif max_height:
        ratio = max_height / height
    else:
        raise PhotoObjectsError(
            "Either max_width or max_height must be specified.")

    # If the image is smaller than the target size, return the original
    if ratio > 1:
        resized = image
    else:
        new_size = round(width * ratio), round(height * ratio)
        resized = image.resize(new_size, Image.Resampling.LANCZOS)

    b = BytesIO()
    resized.save(b, _image_format(filename))
    return b
