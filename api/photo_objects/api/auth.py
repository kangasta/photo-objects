from django.http import HttpRequest

from photo_objects import Size
from photo_objects.models import Album, Photo

from photo_objects.api.utils import (
    AlbumNotFound,
    InvalidSize,
    PhotoNotFound,
    Unauthorized
)


def check_album_access(request: HttpRequest, album_key: str):
    try:
        album = Album.objects.get(key=album_key)
    except Album.DoesNotExist:
        raise AlbumNotFound(album_key)

    if not request.user.is_authenticated:
        if album.visibility != Album.Visibility.PUBLIC:
            raise AlbumNotFound(album_key)

    return album


def check_photo_access(
        request: HttpRequest,
        album_key: str,
        photo_key: str,
        size_key: str):
    try:
        size = Size(size_key)
    except ValueError:
        raise InvalidSize(size_key)

    try:
        album = Album.objects.get(key=album_key)
    except Album.DoesNotExist:
        raise AlbumNotFound(album_key)

    if not request.user.is_authenticated:
        if album.visibility == Album.Visibility.PRIVATE:
            raise AlbumNotFound(album_key)
        if size == Size.ORIGINAL:
            raise Unauthorized()

    try:
        photo = Photo.objects.get(key=photo_key, album__key=album_key)
        return photo
    except Photo.DoesNotExist:
        raise PhotoNotFound(album_key, photo_key)
