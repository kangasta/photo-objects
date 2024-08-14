from django.http import HttpRequest

from photo_objects.models import Photo

from .auth import check_album_access


def get_photos(request: HttpRequest, album_key: str):
    check_album_access(request, album_key)
    return Photo.objects.filter(album__key=album_key)
