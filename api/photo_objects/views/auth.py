from django.http import HttpRequest, HttpResponse

from photo_objects import Size
from photo_objects.models import Album

from ._utils import AlbumNotFound, InvalidSize, JsonProblem, Unauthorized


def _check_album_access(request: HttpRequest, album_key: str, size_key):
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


def has_permission(request: HttpRequest):
    '''Check if user has permission to access photo in given path.

    This view is used with nginx `auth_request` directive and will thus return
    403 status code in all error situations instead of a more suitable status
    code.
    '''
    path = request.GET.get('path')
    try:
        album_key, _, raw_size = path.lstrip('/').split('/')
    except (AttributeError, ValueError):
        return HttpResponse(status=403)

    try:
        _check_album_access(request, album_key, raw_size)
        return HttpResponse(status=204)
    except JsonProblem:
        return HttpResponse(status=403)
