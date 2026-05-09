from uuid import UUID
from django.http import HttpRequest

from photo_objects.django.conf import PhotoSize
from photo_objects.django.models import Album, Photo

from photo_objects.django.api.utils import (
    AlbumNotFound,
    InvalidSize,
    PhotoNotFound,
    PhotoNotFoundByUUID,
    Unauthorized,
    join_key,
)


def _check_album_access(
    request: HttpRequest,
    album: Album,
    album_not_found_exception: Exception,
) -> Album:
    if not request.user.is_authenticated:
        if album.visibility == Album.Visibility.PRIVATE:
            raise album_not_found_exception

    if not request.user.is_staff:
        if album.visibility == Album.Visibility.ADMIN:
            raise album_not_found_exception

    return album


def check_album_access(request: HttpRequest, album_key: str) -> Album:
    try:
        album = Album.objects.get(key=album_key)
    except Album.DoesNotExist:
        raise AlbumNotFound(album_key) from None

    return _check_album_access(request, album, AlbumNotFound(album_key))


def _check_photo_access(
    request: HttpRequest,
    photo: Photo,
    size_key: str,
    album_not_found_exception: Exception,
) -> Photo:
    try:
        size = PhotoSize(size_key)
    except ValueError:
        raise InvalidSize(size_key) from None

    _check_album_access(request, photo.album, album_not_found_exception)

    if not request.user.is_authenticated:
        if size == PhotoSize.ORIGINAL:
            raise Unauthorized()

    return photo


def check_photo_access(
    request: HttpRequest,
    album_key: str,
    photo_key: str,
    size_key: str,
) -> Photo:
    try:
        photo = Photo.objects.get(key=join_key(album_key, photo_key))
    except Photo.DoesNotExist:
        raise PhotoNotFound(album_key, photo_key) from None

    return _check_photo_access(
        request,
        photo,
        size_key,
        AlbumNotFound(album_key)
    )


def check_photo_access_by_uuid(
        request: HttpRequest,
        photo_uuid: UUID,
        size_key: str):
    try:
        photo = Photo.objects.get(uuid=photo_uuid)
    except Photo.DoesNotExist:
        raise PhotoNotFoundByUUID(photo_uuid) from None

    return _check_photo_access(
        request,
        photo,
        size_key,
        PhotoNotFoundByUUID(photo_uuid)
    )
