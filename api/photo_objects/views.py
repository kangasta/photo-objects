import json

from django.contrib.auth.decorators import permission_required
from django.http import HttpRequest, HttpResponse, JsonResponse

from .constants import APPLICATION_JSON
from .errors import JsonProblem
from .models import Album

def _check_permission(request: HttpRequest, permission: str):
    if not request.user.is_authenticated:
        raise JsonProblem(
            "Not authenticated.",
            401,
        )
    if not request.user.has_perm(permission):
        raise JsonProblem(
            f"Expected {permission} permission",
            403,
            headers=dict(Allow="GET, POST")
        )


def _parse_json_body(request: HttpRequest):
    if request.content_type != APPLICATION_JSON:
        raise JsonProblem(
            f"Expected {APPLICATION_JSON} content-type, got {request.content_type}.",
            415,
            headers=dict(Accept=APPLICATION_JSON)
        )

    try:
        return json.loads(request.body)
    except:
        raise JsonProblem(
            "Could not parse JSON data from request body.",
            400,
        )


def albums(request: HttpRequest):
    if request.method == "GET":
        return get_albums(request)
    elif request.method =="POST":
        return create_album(request)
    else:
        return JsonProblem(
            f"Expected GET or POST method, got {request.method}.",
            405,
            headers=dict(Allow="GET, POST")
        ).json_response


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


def has_permission(request: HttpRequest):
    path = request.GET.get('path')
    try:
        album_key, size, _ = path.lstrip('/').split('/')
    except (AttributeError, ValueError):
        return HttpResponse(status=400)

    # TODO: define allowed sizes

    try:
        album = Album.objects.get(key=album_key)
    except Album.DoesNotExist:
        return HttpResponse(status=404)

    if not request.user.is_authenticated:
        if album.visibility == Album.Visibility.PRIVATE:
            return HttpResponse(status=404)
        if size == 'original':
            return HttpResponse(status=401)

    return HttpResponse(status=204)
