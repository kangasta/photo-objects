from django.http import HttpRequest, HttpResponse, JsonResponse

from photo_objects.django import api
from photo_objects.django.api.utils import MethodNotAllowed

from .utils import json_problem_as_json


@json_problem_as_json
def albums(request: HttpRequest):
    if request.method == "GET":
        return get_albums(request)
    elif request.method == "POST":
        return create_album(request)
    else:
        raise MethodNotAllowed(["GET", "POST"], request.method)


def get_albums(request: HttpRequest):
    albums = api.get_albums(request)
    return JsonResponse([i.to_json() for i in albums], safe=False)


def create_album(request: HttpRequest):
    album = api.create_album(request)
    return JsonResponse(album.to_json(), status=201)


@json_problem_as_json
def album(request: HttpRequest, album_key: str):
    if request.method == "GET":
        return get_album(request, album_key)
    elif request.method == "PATCH":
        return modify_album(request, album_key)
    elif request.method == "DELETE":
        return delete_album(request, album_key)
    else:
        raise MethodNotAllowed(
            ["GET", "PATCH", "DELETE"], request.method)


def get_album(request: HttpRequest, album_key: str):
    album = api.check_album_access(request, album_key)
    return JsonResponse(album.to_json())


def modify_album(request: HttpRequest, album_key: str):
    album = api.modify_album(request, album_key)
    return JsonResponse(album.to_json())


def delete_album(request: HttpRequest, album_key: str):
    api.delete_album(request, album_key)
    return HttpResponse(status=204)
