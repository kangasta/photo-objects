from django.http import HttpResponse, JsonResponse

from .models import Album

def get_albums(request):
    albums = Album.objects.all()

    if not request.user.is_authenticated:
        albums = Album.objects.exclude(public=False)

    return JsonResponse([i.to_json() for i in albums], safe=False)

def has_permission(request):
    path = request.GET.get('path')
    try:
        size, album_key, _ = path.lstrip('/').split('/')
    except (AttributeError, ValueError):
        return HttpResponse(status=400)

    # TODO: define allowed sizes

    # TODO: handle not found
    album = Album.objects.get(key=album_key)

    if not request.user.is_authenticated and (size == 'original' or album.public == False):
        return HttpResponse(status=403)

    return HttpResponse(status=204)
