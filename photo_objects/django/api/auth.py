from django.http import HttpRequest

from photo_objects.django import Size
from photo_objects.django.models import Album, Photo

from photo_objects.django.api.utils import (
    AlbumNotFound,
    InvalidSize,
    PhotoNotFound,
    Unauthorized,
    join_key,
)


def check_album_access(request: HttpRequest, album_key: str):
    try:
        album = Album.objects.get(key=album_key)
    except Album.DoesNotExist:
        raise AlbumNotFound(album_key)

    if not request.user.is_authenticated:
        if album.visibility == Album.Visibility.PRIVATE:
            raise AlbumNotFound(album_key)

    if not request.user.is_staff:
        if album.visibility == Album.Visibility.ADMIN:
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
        photo = Photo.objects.get(key=join_key(album_key, photo_key))
    except Photo.DoesNotExist:
        raise PhotoNotFound(album_key, photo_key)

    if not request.user.is_authenticated:
        if photo.album.visibility == Album.Visibility.PRIVATE:
            raise AlbumNotFound(album_key)
        if size == Size.ORIGINAL:
            raise Unauthorized()

    return photo
