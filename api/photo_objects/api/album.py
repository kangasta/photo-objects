from django.http import HttpRequest

from photo_objects.forms import CreateAlbumForm
from photo_objects.models import Album

from .utils import (
    APPLICATION_JSON,
    APPLICATION_X_WWW_FORM,
    FormValidationFailed,
    UnsupportedMediaType,
    check_permissions,
    parse_json_body,
)


def get_albums(request: HttpRequest):
    if not request.user.is_authenticated:
        return Album.objects.filter(visibility=Album.Visibility.PUBLIC)
    else:
        return Album.objects.all()


def create_album(request: HttpRequest):
    check_permissions(request, 'photo_objects.add_album')

    if request.content_type == APPLICATION_JSON:
        data = parse_json_body(request)
    elif request.content_type == APPLICATION_X_WWW_FORM:
        data = request.POST
    else:
        raise UnsupportedMediaType(
            [APPLICATION_JSON, APPLICATION_X_WWW_FORM], request.content_type)

    f = CreateAlbumForm(data)
    if not f.is_valid():
        raise FormValidationFailed(f)

    return f.save()
