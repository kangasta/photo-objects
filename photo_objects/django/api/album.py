import re

from django.contrib.sites.models import Site
from django.db.models.deletion import ProtectedError
from django.http import HttpRequest

from photo_objects.django.forms import CreateAlbumForm, ModifyAlbumForm
from photo_objects.django.models import Album

from .auth import check_album_access
from .utils import (
    FormValidationFailed,
    JsonProblem,
    check_permissions,
    parse_input_data,
)


def get_site_album(site: Site) -> tuple[Album, bool]:
    album_key = f'_site_{site.id}'
    return Album.objects.get_or_create(
        key=album_key,
        defaults={
            'title': site.name,
            'visibility': Album.Visibility.ADMIN,
        })


def parse_site_id(album_key: str) -> int | None:
    key_match = re.match(r'_site_([0-9]+)', album_key)
    if not key_match:
        return None

    return int(key_match.group(1))


def get_albums(request: HttpRequest):
    if not request.user.is_authenticated:
        return Album.objects.filter(visibility=Album.Visibility.PUBLIC)
    if request.user.is_staff:
        return Album.objects.all()

    return Album.objects.filter(visibility__in=[
        Album.Visibility.PUBLIC,
        Album.Visibility.HIDDEN,
        Album.Visibility.PRIVATE,
    ])


def create_album(request: HttpRequest):
    check_permissions(request, 'photo_objects.add_album')
    data = parse_input_data(request)

    f = CreateAlbumForm(data, user=request.user)
    if not f.is_valid():
        raise FormValidationFailed(f)

    return f.save()


def modify_album(request: HttpRequest, album_key: str):
    check_permissions(request, 'photo_objects.change_album')
    album = check_album_access(request, album_key)
    data = parse_input_data(request)

    f = ModifyAlbumForm({**album.to_json(), **data},
                        instance=album, user=request.user)
    if not f.is_valid():
        raise FormValidationFailed(f)

    return f.save()


def delete_album(request: HttpRequest, album_key: str):
    check_permissions(request, 'photo_objects.delete_album')
    album = check_album_access(request, album_key)

    if album.key.startswith('_'):
        raise JsonProblem(
            f"Album with {album_key} key is managed by the system and can not "
            "be deleted.",
            409,
        )

    try:
        album.delete()
    except ProtectedError:
        raise JsonProblem(
            f"Album with {album_key} key can not be deleted because it "
            "contains photos.",
            409,
        ) from None
