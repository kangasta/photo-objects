from django.db.models.deletion import ProtectedError
from django.http import HttpRequest

from photo_objects.forms import CreateAlbumForm, ModifyAlbumForm
from photo_objects.models import Album

from .auth import check_album_access
from .utils import (
    FormValidationFailed,
    JsonProblem,
    check_permissions,
    parse_input_data,
)


def get_albums(request: HttpRequest):
    if not request.user.is_authenticated:
        return Album.objects.filter(visibility=Album.Visibility.PUBLIC)
    else:
        return Album.objects.all()


def create_album(request: HttpRequest):
    check_permissions(request, 'photo_objects.add_album')
    data = parse_input_data(request)

    f = CreateAlbumForm(data)
    if not f.is_valid():
        raise FormValidationFailed(f)

    return f.save()


def modify_album(request: HttpRequest, album_key: str):
    check_permissions(request, 'photo_objects.change_album')
    album = check_album_access(request, album_key)
    data = parse_input_data(request)

    f = ModifyAlbumForm({**album.to_json(), **data}, instance=album)
    if not f.is_valid():
        raise FormValidationFailed(f)

    return f.save()


def delete_album(request: HttpRequest, album_key: str):
    check_permissions(request, 'photo_objects.delete_album')
    album = check_album_access(request, album_key)

    try:
        album.delete()
    except ProtectedError:
        raise JsonProblem(
            f"Album with {album_key} key can not be deleted because it "
            "contains photos.",
            409,
        )
