from django.http import HttpRequest

from photo_objects.django.conf import PhotoSize
from photo_objects.django.models import Album, Photo

from photo_objects.django.api.utils import (
    AlbumNotFound,
    InvalidSize,
    PhotoNotFound,
    Unauthorized,
    join_key,
)


def _check_album_access(request: HttpRequest, album: Album) -> Album:
    if not request.user.is_authenticated:
        if album.visibility == Album.Visibility.PRIVATE:
            raise AlbumNotFound(album.key)

    if not request.user.is_staff:
        if album.visibility == Album.Visibility.ADMIN:
            raise AlbumNotFound(album.key)

    return album


def check_album_access(request: HttpRequest, album_key: str) -> Album:
    try:
        album = Album.objects.get(key=album_key)
    except Album.DoesNotExist:
        raise AlbumNotFound(album_key) from None

    return _check_album_access(request, album)


def check_photo_access(
        request: HttpRequest,
        album_key: str,
        photo_key: str,
        size_key: str) -> Photo:
    try:
        size = PhotoSize(size_key)
    except ValueError:
        raise InvalidSize(size_key) from None

    try:
        photo = Photo.objects.get(key=join_key(album_key, photo_key))
    except Photo.DoesNotExist:
        raise PhotoNotFound(album_key, photo_key) from None

    _check_album_access(request, photo.album)

    if not request.user.is_authenticated:
        if size == PhotoSize.ORIGINAL:
            raise Unauthorized()

    return photo
