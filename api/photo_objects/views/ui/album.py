from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from photo_objects import api
from photo_objects.api.utils import JsonProblem


def list_albums(request: HttpRequest):
    albums = api.get_albums(request)
    return render(request, "photo_objects/list_albums.html", {"albums": albums})


def new_album(request: HttpRequest):
    return HttpResponse("new_album")


def show_album(request: HttpRequest, album_key: str):
    try:
        album = api.check_album_access(request, album_key)
        photos = api.get_photos(request, album_key)
    except JsonProblem as e:
        return e.html_response(request)

    return render(request, "photo_objects/show_album.html", {"album": album, "photos": photos})


def edit_album(request: HttpRequest, album_key: str):
    return HttpResponse("edit_album")


def delete_album(request: HttpRequest, album_key: str):
    return HttpResponse("delete_album")
