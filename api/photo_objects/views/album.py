from django.http import HttpRequest, JsonResponse

from photo_objects.models import Album

from ._utils import (
    Conflict,
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


def create_album(request: HttpRequest):
    try:
        _check_permissions(request, 'photo_objects.add_album')
        data = _parse_json_body(request)
    except JsonProblem as e:
        return e.json_response

    key = data.get("key")
    if len(key) == 0:
        return JsonProblem(
            f"Key must be specified.",
            400,
        ).json_response
    if Album.objects.filter(key=key).exists():
        return Conflict(
            f"Album with {key} key already exists.",
        ).json_response

    album = Album.objects.create(
        key=data.get("key"),
        visibility=data.get("visibility", Album.Visibility.PRIVATE),
        title=data.get("title", ""),
        description=data.get("description", ""),
    )

    return JsonResponse(album.to_json(), status=201)


def get_albums(request: HttpRequest):
    if not request.user.is_authenticated:
        albums = Album.objects.filter(visibility=Album.Visibility.PUBLIC)
    else:
        albums = Album.objects.all()

    return JsonResponse([i.to_json() for i in albums], safe=False)
