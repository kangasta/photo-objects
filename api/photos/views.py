from django.http import HttpResponse, JsonResponse

from .models import Album

def get_albums(request):
    albums = Album.objects.all()

    if not request.user.is_authenticated:
        albums = Album.objects.exclude(public=False)

    return JsonResponse([i.to_json() for i in albums], safe=False)

def has_permission(request):
    path = request.GET.get('path')
    if not path:
        return HttpResponse(status=400)

    album_key, _ = path.split('/')
    album = Album.objects.get(key=album_key)
    if album.public == False and not request.user.is_authenticated:
        return HttpResponse(status=403)

    return HttpResponse(status=204)
