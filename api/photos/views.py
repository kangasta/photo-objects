from django.http import HttpResponse, JsonResponse

from .models import Album, Photo

def get_albums(request):
    albums = Album.objects.all()

    if not request.user.is_authenticated:
        albums = Album.objects.exclude(public=False)

    return JsonResponse([i.to_json() for i in albums], safe=False)

def get_pending_photos(_):
    photos = Photo.objects.filter(tiny_base64="")

    return JsonResponse([i.to_json() for i in photos], safe=False)

def has_permission(request):
    path = request.GET.get('path')
    try:
        size, album_key, _ = path.lstrip('/').split('/')
    except (AttributeError, ValueError):
        return HttpResponse(status=400)

    # TODO: define allowed sizes

    try:
        album = Album.objects.get(key=album_key)
    except Album.DoesNotExist:
        return HttpResponse(status=404)

    if not request.user.is_authenticated:
        if album.public == False:
            return HttpResponse(status=404)
        if size == 'original':
            return HttpResponse(status=401)

    return HttpResponse(status=204)
