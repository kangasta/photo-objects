from django.http import HttpRequest
from minio.error import S3Error
from PIL import UnidentifiedImageError

from photo_objects import objsto
from photo_objects.forms import CreatePhotoForm, ModifyPhotoForm
from photo_objects.img import photo_details
from photo_objects.models import Photo

from .auth import check_album_access, check_photo_access
from .utils import (
    JsonProblem,
    check_permissions,
    parse_input_data,
    parse_single_file,
)


def get_photos(request: HttpRequest, album_key: str):
    check_album_access(request, album_key)
    return Photo.objects.filter(album__key=album_key)


def upload_photo(request: HttpRequest, album_key: str):
    check_permissions(
        request,
        'photo_objects.add_photo',
        'photo_objects.change_album')
    photo_file = parse_single_file(request)

    try:
        timestamp, tiny_base64 = photo_details(photo_file)
    except UnidentifiedImageError:
        raise JsonProblem(
            "Could not open photo file.",
            400,
        )

    f = CreatePhotoForm(dict(
        key=photo_file.name,
        album=album_key,
        title="",
        description="",
        timestamp=timestamp,
        tiny_base64=tiny_base64,
    ))

    if not f.is_valid():
        raise JsonProblem(
            "Photo validation failed.",
            400,
            errors=f.errors.get_json_data(),
        )
    photo = f.save()

    photo_file.seek(0)
    try:
        objsto.put_photo(photo.album.key, photo.key, "og", photo_file)
    except S3Error:
        # TODO: logging
        raise JsonProblem(
            "Could not save photo to object storage.",
            500,
        )

    return photo


def modify_photo(request: HttpRequest, album_key: str, photo_key: str):
    check_permissions(request, 'photo_objects.change_photo')
    photo = check_photo_access(request, album_key, photo_key, 'xs')
    data = parse_input_data(request)

    f = ModifyPhotoForm({**photo.to_json(), **data}, instance=photo)

    if not f.is_valid():
        raise JsonProblem(
            "Photo validation failed.",
            400,
            errors=f.errors.get_json_data(),
        )

    return f.save()


def delete_photo(request: HttpRequest, album_key: str, photo_key: str):
    check_permissions(request, 'photo_objects.delete_photo')
    photo = check_photo_access(request, album_key, photo_key, 'xs')

    try:
        objsto.delete_photo(album_key, photo_key)
    except S3Error:
        raise JsonProblem(
            "Could not delete photo from object storage.",
            500,
        )

    try:
        photo.delete()
    except Exception:
        raise JsonProblem(
            "Could not delete photo from database.",
            500,
        )
