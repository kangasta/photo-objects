from django.http import HttpRequest, HttpResponse, JsonResponse

from photo_objects.models import Album

from ._utils import (
    JsonProblem,
    MethodNotAllowed,
    _check_permission,
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
        _check_permission(request, 'photo_objects.add_album')
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
        return JsonProblem(
            f"Album with given key already exists.",
            409,
        ).json_response

    album = Album.objects.create(
        key=data.get("key"),
        visibility=data.get("visibility", Album.Visibility.PRIVATE),
        title=data.get("title", ""),
        description=data.get("description", ""),
    )

    return JsonResponse(album.to_json(), status=201)


def get_albums(request: HttpRequest):
    albums = Album.objects.all()

    if not request.user.is_authenticated:
        albums = Album.objects.filter(visibility=Album.Visibility.PUBLIC)

    return JsonResponse([i.to_json() for i in albums], safe=False)
