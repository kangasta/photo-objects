from base64 import b64encode
try:
    from datetime import datetime, UTC
except ImportError:
    from datetime import datetime, timezone
    UTC = timezone.utc
from io import BytesIO

from PIL import Image, ExifTags

from photo_objects.error import PhotoObjectsError


def utcnow():
    '''Return timezone aware datetime object with current UTC time.
    '''
    return datetime.now(UTC)


class ExifReader:
    def __init__(self, image: Image):
        self.image = image
        self._data = [
            image.getexif(),
            image.getexif().get_ifd(ExifTags.IFD.Exif),
        ]

    def get(self, key):
        for d in self._data:
            value = d.get(key)
            if value is not None:
                return value
        return None


def _read_original_datetime(image: Image) -> datetime:
    try:
        info = ExifReader(image)

        time = info.get(ExifTags.Base.DateTimeOriginal)
        subsec = info.get(ExifTags.Base.SubsecTimeOriginal) or "0"
        offset = info.get(ExifTags.Base.OffsetTimeOriginal) or "+00:00"

        return datetime.strptime(
            f"{time}.{subsec}{offset}",
            "%Y:%m:%d %H:%M:%S.%f%z")
    except BaseException:
        return None


def _read_camera_setup_and_settings(image: Image) -> dict:
    try:
        info = ExifReader(image)

        return dict(
            camera_make=info.get(ExifTags.Base.Make),
            camera_model=info.get(ExifTags.Base.Model),
            lens_make=info.get(ExifTags.Base.LensMake),
            lens_model=info.get(ExifTags.Base.LensModel),
            focal_length=info.get(ExifTags.Base.FocalLength),
            f_number=info.get(ExifTags.Base.FNumber),
            exposure_time=info.get(ExifTags.Base.ExposureTime),
            iso_speed=info.get(ExifTags.Base.ISOSpeedRatings),
        )
    except Exception as e:
        raise e


def _image_format(image_format, filename):
    if image_format:
        return image_format

    image_format = filename.split('.')[-1].upper()

    if image_format == "JPG":
        return "JPEG"

    return image_format


def photo_details(photo_file):
    image = Image.open(photo_file)

    width, height = image.size
    timestamp = _read_original_datetime(image) or utcnow()
    camera_setup_and_settings = _read_camera_setup_and_settings(image)

    # TODO: remove all extra data from the image
    resized = image.resize((3, 3))

    b = BytesIO()
    resized.save(b, format='PNG', optimize=True, icc_profile=None)

    return dict(
        timestamp=timestamp,
        width=width,
        height=height,
        tiny_base64=b64encode(b.getvalue()).decode('ascii'),
        **camera_setup_and_settings,
    )


def _calculate_box(
    width,
    height,
    max_aspect_ratio
) -> tuple[float, float, float, float]:
    if max_aspect_ratio is None:
        return None

    min_aspect_ratio = 1.0 / max_aspect_ratio

    aspect_ratio = width / height

    if aspect_ratio > max_aspect_ratio:
        new_width = height * max_aspect_ratio
        crop_amount = width - new_width
        left = round(crop_amount / 2)
        right = round(width - crop_amount / 2)
        return (left, 0, right, height)

    if aspect_ratio < min_aspect_ratio:
        new_height = width / min_aspect_ratio
        crop_amount = height - new_height
        top = round(crop_amount / 2)
        bottom = round(height - crop_amount / 2)
        return (0, top, width, bottom)

    return None


def scale_photo(
        photo_file,
        filename,
        max_width=None,
        max_height=None,
        max_aspect_ratio=None,
        image_format=None):
    image = Image.open(photo_file)
    width, height = image.size

    # Crop image if aspect ratio is:
    # - greater than max_aspect_ratio, or
    # - less than 1/max_aspect_ratio
    box = _calculate_box(width, height, max_aspect_ratio)
    if box:
        image = image.crop(box)
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
    resized.save(b, _image_format(image_format, filename))
    return b
