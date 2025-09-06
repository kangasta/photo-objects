from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from photo_objects.django import api
from photo_objects.django.api.utils import FormValidationFailed
from photo_objects.django.forms import CreateAlbumForm, ModifyAlbumForm
from photo_objects.django.models import Album
from photo_objects.django.views.utils import (
    BackLink,
    meta_description,
)
from photo_objects.utils import render_markdown

from .utils import json_problem_as_html


@json_problem_as_html
def list_albums(request: HttpRequest):
    albums = api.get_albums(request)
    return render(request, "photo_objects/album/list.html", {
        "albums": albums,
        "title": "Albums",
    })


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
        form = CreateAlbumForm(initial={"key": "_new"}, user=request.user)

    back = BackLink("Back to albums", reverse('photo_objects:list_albums'))

    return render(request, 'photo_objects/form.html', {
        "form": form,
        "title": "Create album",
        "back": back,
    })


def get_info(request: HttpRequest, album_key: str):
    # TODO: Remove this later if not needed
    return None


@json_problem_as_html
def show_album(request: HttpRequest, album_key: str):
    album = api.check_album_access(request, album_key)
    photos = album.photo_set.all()

    back = BackLink("Back to albums", reverse('photo_objects:list_albums'))
    details = {
        "Description": render_markdown(album.description),
        "Visibility": Album.Visibility(album.visibility).label,
    }

    return render(request, "photo_objects/album/show.html", {
        "album": album,
        "photos": photos,
        "title": album.title or album.key,
        "description": meta_description(request, album),
        "back": back,
        "details": details,
        "photo": album.cover_photo,
        "info": get_info(request, album_key),
    })


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
            instance=album,
            user=request.user)

    target = album.title or album.key
    back = BackLink(
        f'Back to {target}',
        reverse(
            'photo_objects:show_album',
            kwargs={"album_key": album_key}))

    return render(request, 'photo_objects/form.html', {
        "form": form,
        "title": "Edit album",
        "back": back,
        "photo": album.cover_photo,
        "info": get_info(request, album_key),
    })


@json_problem_as_html
def delete_album(request: HttpRequest, album_key: str):
    if request.method == "POST":
        api.delete_album(request, album_key)
        return HttpResponseRedirect(reverse('photo_objects:list_albums'))
    else:
        album = api.check_album_access(request, album_key)
        target = album.title or album.key
        back = BackLink(
            f'Back to {target}',
            reverse(
                'photo_objects:show_album',
                kwargs={
                    "album_key": album_key}))

        error = {}
        if album.photo_set.count() > 0:
            error = {'error': _(
                'Album can not be deleted because it contains photos. Delete '
                'all photos from the album to be able to delete the album.')}
        if album.key.startswith('_'):
            error = {'error': _(
                'This album is managed by the system and can not be deleted.')}

    return render(request, 'photo_objects/delete.html', {
        "title": "Delete album",
        "back": back,
        "photo": album.cover_photo,
        "resource": target,
        **error,
    })
