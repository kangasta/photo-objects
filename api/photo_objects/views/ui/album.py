from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from photo_objects import api
from photo_objects.api.utils import FormValidationFailed
from photo_objects.forms import CreateAlbumForm, ModifyAlbumForm

from .utils import BackLink, json_problem_as_html


@json_problem_as_html
def list_albums(request: HttpRequest):
    albums = api.get_albums(request)
    return render(request,
                  "photo_objects/album/list.html",
                  {"albums": albums})


@json_problem_as_html
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

    back = BackLink("Back to albums", reverse('photo_objects:list_albums'))

    return render(request, 'photo_objects/form.html',
                  {"form": form, "title": "Create album", "back": back})


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
        cover_photo = album.cover_photo.key if album.cover_photo else None
        form = ModifyAlbumForm(
            initial={
                **album.to_json(),
                'cover_photo': cover_photo},
            instance=album)

    target = album.title or album.key
    back = BackLink(
        f'Back to {target}',
        reverse(
            'photo_objects:show_album',
            kwargs={"album_key": album_key}))

    return render(request, 'photo_objects/form.html',
                  {"form": form, "title": "Edit album", "back": back})


@json_problem_as_html
def delete_album(request: HttpRequest, album_key: str):
    if request.method == "POST":
        api.delete_album(request, album_key)
        return HttpResponseRedirect(reverse('photo_objects:list_albums'))
    else:
        album = api.check_album_access(request, album_key)
        target = album.title or album.filename
        back = BackLink(
            f'Back to {target}',
            reverse(
                'photo_objects:show_album',
                kwargs={
                    "album_key": album_key}))

    return render(request, 'photo_objects/delete.html', {
        "target": target,
        "back": back})
