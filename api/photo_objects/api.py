from django.http import HttpRequest

from photo_objects.models import Album

def get_albums(request: HttpRequest):
    if not request.user.is_authenticated:
        return Album.objects.filter(visibility=Album.Visibility.PUBLIC)
    else:
        return Album.objects.all()
