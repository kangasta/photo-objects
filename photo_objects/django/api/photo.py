from django.core.files.uploadedfile import UploadedFile
from django.http import HttpRequest
from minio.error import S3Error
from PIL import UnidentifiedImageError
from urllib3.exceptions import HTTPError

from photo_objects import logger
from photo_objects.django import objsto
from photo_objects.django.forms import (
    CreatePhotoForm,
    ModifyPhotoForm,
    UploadPhotosForm,
    slugify,
)
from photo_objects.img import photo_details

from .auth import check_album_access, check_photo_access
from .utils import (
    FormValidationFailed,
    UploadPhotosFailed,
    JsonProblem,
    check_permissions,
    parse_input_data,
    parse_single_file,
)


def get_photos(request: HttpRequest, album_key: str):
    album = check_album_access(request, album_key)
    return album.photo_set.all()


def _upload_photo(album_key: str, photo_file: UploadedFile):
    try:
        details = photo_details(photo_file)
    except UnidentifiedImageError:
        raise JsonProblem(
            "Could not open photo file.",
            400,
        ) from None

    f = CreatePhotoForm(dict(
        key=f"{album_key}/{slugify(photo_file.name)}",
        album=album_key,
        title="",
        description="",
        **details,
    ))

    if not f.is_valid():
        raise FormValidationFailed(f)
    photo = f.save()

    photo_file.seek(0)
    try:
        objsto.put_photo(photo.album.key, photo.filename, "og", photo_file)
    except (S3Error, HTTPError) as e:
        photo.delete()

        msg = objsto.with_error_code(
            "Could not save photo to object storage.", e)
        logger.error(f"{msg}: {str(e)}")
        raise JsonProblem(f"{msg}.", 500) from e

    return photo


def upload_photo(request: HttpRequest, album_key: str):
    check_permissions(
        request,
        'photo_objects.add_photo',
        'photo_objects.change_album')
    photo_file = parse_single_file(request)
    return _upload_photo(album_key, photo_file)


def _join_errors(errors: dict) -> str:
    messages = []
    for _, errs in errors.items():
        for err in errs:
            try:
                messages.append(err.get('message'))
            except AttributeError:
                messages.append(str(err))
    return " ".join(messages) if messages else "Unknown error."


def upload_photos(request: HttpRequest, album_key: str):
    check_permissions(
        request,
        'photo_objects.add_photo',
        'photo_objects.change_album')

    f = UploadPhotosForm(request.POST, request.FILES)
    if not f.is_valid():
        raise FormValidationFailed(f)

    photo_files = f.cleaned_data["photos"]
    if len(photo_files) < 1:
        f.add_error("photos", "Expected at least one file, got 0.")
        raise FormValidationFailed(f)

    photos = []
    for photo_file in f.cleaned_data["photos"]:
        try:
            photos.append(_upload_photo(album_key, photo_file))
        except FormValidationFailed as e:
            message = _join_errors(e.form.errors.get_json_data())
            f.add_error(
                "photos",
                f"Failed to upload {photo_file.name}. {message}")
        except JsonProblem as e:
            f.add_error(
                "photos",
                f"Failed to upload {photo_file.name}. {e.title}")

    if not f.is_valid():
        raise UploadPhotosFailed(f, [i.filename for i in photos])

    return photos


def modify_photo(request: HttpRequest, album_key: str, photo_key: str):
    check_permissions(request, 'photo_objects.change_photo')
    photo = check_photo_access(request, album_key, photo_key, 'xs')
    data = parse_input_data(request)

    f = ModifyPhotoForm({**photo.to_json(), **data}, instance=photo)

    if not f.is_valid():
        raise FormValidationFailed(f)

    return f.save()


def delete_photo(request: HttpRequest, album_key: str, photo_key: str):
    check_permissions(request, 'photo_objects.delete_photo')
    photo = check_photo_access(request, album_key, photo_key, 'xs')

    try:
        objsto.delete_photo(album_key, photo_key)
    except (S3Error, HTTPError) as e:
        msg = objsto.with_error_code(
            "Could not delete photo from object storage", e)
        logger.error(f"{msg}: {str(e)}")
        raise JsonProblem(f"{msg}.", 500) from e

    try:
        photo.delete()
    except Exception as e:
        msg = "Could not delete photo from database"
        logger.error(f"{msg}: {str(e)}")
        raise JsonProblem(f"{msg}.", 500) from e
