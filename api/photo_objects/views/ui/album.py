from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from photo_objects import api
from photo_objects.api.utils import FormValidationFailed, JsonProblem
from photo_objects.forms import CreateAlbumForm


def list_albums(request: HttpRequest):
    albums = api.get_albums(request)
    return render(request,
                  "photo_objects/list_albums.html",
                  {"albums": albums})


def new_album(request: HttpRequest):
    if request.method == "POST":
        try:
            album = api.create_album(request)
            return HttpResponseRedirect(
                reverse(
                    'photo_objects:show_album',
                    kwargs={
                        "album_key": album.key}))
        except FormValidationFailed as e:
            form = e.form
    else:
        form = CreateAlbumForm()

    return render(request, 'photo_objects/new_album.html', {"form": form})


def show_album(request: HttpRequest, album_key: str):
    try:
        album = api.check_album_access(request, album_key)
        photos = api.get_photos(request, album_key)
    except JsonProblem as e:
        return e.html_response(request)

    return render(request, "photo_objects/show_album.html",
                  {"album": album, "photos": photos})


def edit_album(request: HttpRequest, album_key: str):
    return HttpResponse("edit_album")


def delete_album(request: HttpRequest, album_key: str):
    return HttpResponse("delete_album")
