from django.db.models.deletion import ProtectedError
from django.http import HttpRequest, HttpResponse, JsonResponse

from photo_objects import api
from photo_objects.models import Album
from photo_objects.forms import CreateAlbumForm, ModifyAlbumForm

from .auth import _check_album_access
from ._utils import (
    JsonProblem,
    MethodNotAllowed,
    _check_permissions,
    _parse_json_body
)


def albums(request: HttpRequest):
    if request.method == "GET":
        return get_albums(request)
    elif request.method == "POST":
        return create_album(request)
    else:
        return MethodNotAllowed(["GET", "POST"], request.method).json_response


def get_albums(request: HttpRequest):
    albums = api.get_albums(request)
    return JsonResponse([i.to_json() for i in albums], safe=False)


def create_album(request: HttpRequest):
    try:
        _check_permissions(request, 'photo_objects.add_album')
        data = _parse_json_body(request)
    except JsonProblem as e:
        return e.json_response

    f = CreateAlbumForm(data)
    if not f.is_valid():
        return JsonProblem(
            "Album validation failed.",
            400,
            errors=f.errors.get_json_data(),
        ).json_response

    album = f.save()
    return JsonResponse(album.to_json(), status=201)


def album(request: HttpRequest, album_key: str):
    if request.method == "GET":
        return get_album(request, album_key)
    elif request.method == "PATCH":
        return modify_album(request, album_key)
    elif request.method == "DELETE":
        return delete_album(request, album_key)
    else:
        return MethodNotAllowed(
            ["GET", "PATCH", "DELETE"], request.method).json_response


def get_album(request: HttpRequest, album_key: str):
    try:
        album = _check_album_access(request, album_key)
        return JsonResponse(album.to_json())
    except JsonProblem as e:
        return e.json_response


def modify_album(request: HttpRequest, album_key: str):
    try:
        _check_permissions(request, 'photo_objects.change_album')
        album = _check_album_access(request, album_key)
        data = _parse_json_body(request)
    except JsonProblem as e:
        return e.json_response

    f = ModifyAlbumForm({**album.to_json(), **data}, instance=album)
    if not f.is_valid():
        return JsonProblem(
            "Album validation failed.",
            400,
            errors=f.errors.get_json_data(),
        ).json_response

    album = f.save()
    return JsonResponse(album.to_json())


def delete_album(request: HttpRequest, album_key: str):
    try:
        _check_permissions(request, 'photo_objects.delete_album')
        album = _check_album_access(request, album_key)
    except JsonProblem as e:
        return e.json_response

    try:
        album.delete()
    except ProtectedError:
        return JsonProblem(
            f"Album with {album_key} key can not be deleted because it "
            "contains photos.",
            409,
        ).json_response
    return HttpResponse(status=204)
