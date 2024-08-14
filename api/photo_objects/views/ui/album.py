from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from photo_objects import api


def list_albums(request: HttpRequest):
    albums = api.get_albums(request)
    return render(request, "photo_objects/list_albums.html", {"albums": albums})


def new_album(request: HttpRequest):
    return HttpResponse("new_album")


def show_album(request: HttpRequest, album_key: str):
    return HttpResponse("show_album")


def edit_album(request: HttpRequest, album_key: str):
    return HttpResponse("edit_album")


def delete_album(request: HttpRequest, album_key: str):
    return HttpResponse("delete_album")
