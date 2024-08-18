from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from photo_objects import api
from photo_objects.api.utils import FormValidationFailed
from photo_objects.forms import CreateAlbumForm, ModifyAlbumForm

from .utils import json_problem_as_html


def list_albums(request: HttpRequest):
    albums = api.get_albums(request)
    return render(request,
                  "photo_objects/album/list.html",
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
        form = CreateAlbumForm(initial={"key": "_new"})

    return render(request, 'photo_objects/form.html',
                  {"form": form, "title": "Create album"})


@json_problem_as_html
def show_album(request: HttpRequest, album_key: str):
    album = api.check_album_access(request, album_key)
    photos = album.photo_set.all()

    return render(request, "photo_objects/album/show.html",
                  {"album": album, "photos": photos})


@json_problem_as_html
def edit_album(request: HttpRequest, album_key: str):
    if request.method == "POST":
        try:
            album = api.modify_album(request, album_key)
            return HttpResponseRedirect(
                reverse(
                    'photo_objects:show_album',
                    kwargs={
                        "album_key": album.key}))
        except FormValidationFailed as e:
            album = api.check_album_access(request, album_key)
            form = e.form
    else:
        album = api.check_album_access(request, album_key)
        form = ModifyAlbumForm(initial=album.to_json(), instance=album)

    return render(request, 'photo_objects/form.html',
                  {"form": form, "title": "Edit album"})


@json_problem_as_html
def delete_album(request: HttpRequest, album_key: str):
    if request.method == "POST":
        api.delete_album(request, album_key)
        return HttpResponseRedirect(reverse('photo_objects:list_albums'))
    else:
        album = api.check_album_access(request, album_key)
    return render(request, 'photo_objects/album/delete.html', {"album": album})
