from django.http import HttpRequest, HttpResponse

from photo_objects.models import Album


def has_permission(request: HttpRequest):
    path = request.GET.get('path')
    try:
        album_key, size, _ = path.lstrip('/').split('/')
    except (AttributeError, ValueError):
        return HttpResponse(status=400)

    # TODO: define allowed sizes

    try:
        album = Album.objects.get(key=album_key)
    except Album.DoesNotExist:
        return HttpResponse(status=404)

    if not request.user.is_authenticated:
        if album.visibility == Album.Visibility.PRIVATE:
            return HttpResponse(status=404)
        if size == 'original':
            return HttpResponse(status=401)

    return HttpResponse(status=204)
