from django.http import HttpRequest, HttpResponse

from photo_objects import Size
from photo_objects.models import Album


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
        size = Size(raw_size)
    except ValueError:
        return HttpResponse(status=403)

    try:
        album = Album.objects.get(key=album_key)
    except Album.DoesNotExist:
        return HttpResponse(status=403)

    if not request.user.is_authenticated:
        if album.visibility == Album.Visibility.PRIVATE:
            return HttpResponse(status=403)
        if size == Size.ORIGINAL:
            return HttpResponse(status=403)

    return HttpResponse(status=204)
