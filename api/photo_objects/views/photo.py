from base64 import b64encode
from io import BytesIO

from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from PIL import Image, ExifTags

from photo_objects.models import Album, Photo
from photo_objects.object_storage import put_photo

from ._utils import (
    Conflict,
    JsonProblem,
    MethodNotAllowed,
    _check_permissions,
    _parse_single_file,
)


def photos(request: HttpRequest, album_key: str):
    if request.method == "POST":
        return upload_photo(request, album_key)
    else:
        return MethodNotAllowed(["POST"], request.method).json_response


def _read_original_datetime(image: Image) -> timezone.datetime:
    try:
        for key, value in ExifTags.TAGS.items():
            if value == "ExifOffset":
                break

        info = image.getexif().get_ifd(key)

        time = info.get(ExifTags.Base.DateTimeOriginal)
        subsec = info.get(ExifTags.Base.SubsecTimeOriginal) or "0"
        offset = info.get(ExifTags.Base.OffsetTimeOriginal) or "+00:00"

        return timezone.datetime.strptime(
            f"{time}.{subsec}{offset}",
            "%Y:%m:%d %H:%M:%S.%f%z")
    except BaseException:
        return None


def upload_photo(request: HttpRequest, album_key: str):
    try:
        _check_permissions(
            request,
            'photo_objects.add_photo',
            'photo_objects.change_album')
        photo_file = _parse_single_file(request)
    except JsonProblem as e:
        return e.json_response

    try:
        album = Album.objects.get(key=album_key)
    except Album.DoesNotExist:
        return JsonProblem(
            f"Album with {album_key} key does not exist.",
            404,
        ).json_response

    key = photo_file.name
    if Photo.objects.filter(key=key).exists():
        return Conflict(
            f"Photo with {key} key already exists in {album_key} album.",
        ).json_response

    image = Image.open(photo_file)
    timestamp = _read_original_datetime(image) or timezone.now()

    b = BytesIO()
    image.save(b, format='PNG')
    tiny_base64 = b64encode(b.getvalue())

    photo = Photo.objects.create(
        key=key,
        album=album,
        title="",
        description="",
        timestamp=timestamp,
        tiny_base64=tiny_base64,
    )

    photo_file.seek(0)
    try:
        put_photo(album.key, photo.key, "og", photo_file)
    except BaseException:
        # TODO: logging
        return JsonProblem(
            "Could not save photo to object storage.",
            500,
        ).json_response

    return JsonResponse(photo.to_json(), status=201)
