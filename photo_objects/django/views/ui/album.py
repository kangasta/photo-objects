from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from photo_objects.django import api
from photo_objects.django.api.utils import FormValidationFailed
from photo_objects.django.forms import CreateAlbumForm, ModifyAlbumForm
from photo_objects.django.models import Album, SiteSettings, Visibility
from photo_objects.django.views.utils import (
    BackLink,
    Preview,
    meta_description,
)
from photo_objects.utils import render_markdown

from .utils import json_problem_as_html, preview_helptext, year_month


def _group_albums(
    albums: list[Album],
    group_by: str,
) -> dict[str, list[Album]]:
    if len(albums) == 0:
        return {}

    if group_by == "year":
        result = {}
        for album in albums:
            key = str(
                album.first_timestamp.year) if album.first_timestamp else ""
            result.setdefault(key, []).append(album)
        return result
    if group_by == "month":
        result = {}
        for album in albums:
            if album.first_timestamp is None:
                key = ""
            else:
                key = year_month(album.first_timestamp)
            result.setdefault(key, []).append(album)
        return result
    else:
        return {"": albums}


@json_problem_as_html
def list_albums(request: HttpRequest):
    try:
        settings = SiteSettings.objects.get(request.site)
        group_by = settings.albums_group_by
    except SiteSettings.DoesNotExist:
        group_by = "none"

    actions = []
    if request.user.has_perm("photo_objects.add_album"):
        actions.append({
            "label": "New album",
            "target": reverse('photo_objects:new_album'),
        })

    albums = api.get_albums(request)
    return render(request, "photo_objects/collection/list.html", {
        "grouped_collections": _group_albums(albums, group_by),
        "title": "Albums",
        "type": "albums",
        "show_name": "photo_objects:show_album",
        "actions": actions,
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

    back = BackLink("Albums", reverse('photo_objects:list_albums'))

    return render(request, 'photo_objects/form.html', {
        "form": form,
        "title": "Create album",
        "back": back,
        "width": "narrow",
    })


def get_info(request: HttpRequest, album_key: str):
    # TODO: Remove this later if not needed
    return None


def _timeline(album: Album):
    if not album.first_timestamp or not album.last_timestamp:
        return None

    start = album.first_timestamp.strftime("%Y %B")
    end = album.last_timestamp.strftime("%Y %B")

    if start == end:
        return start
    return f"{start} – {end}"


@json_problem_as_html
def show_album(request: HttpRequest, album_key: str):
    album = api.check_album_access(request, album_key)
    photos = album.photo_set.all()

    back = BackLink("Albums", reverse('photo_objects:list_albums'))
    details = {
        "Description": render_markdown(album.description),
        "Timeline": _timeline(album),
        "Visibility": Visibility(album.visibility).label,
        "Created at": album.created_at,
        "Updated at": album.updated_at,
    }

    actions = []
    if request.user.has_perm("photo_objects.change_album"):
        if request.user.has_perm("photo_objects.add_photo"):
            actions.append({
                "label": "Upload photos",
                "target": reverse(
                    'photo_objects:upload_photos',
                    kwargs={"album_key": album.key},
                ),
            })

        actions.append({
            "label": "Edit album",
            "target": reverse(
                'photo_objects:edit_album',
                kwargs={"album_key": album.key},
            ),
        })

    if request.user.has_perm("photo_objects.delete_album"):
        actions.append({
            "label": "Delete album",
            "target": reverse(
                'photo_objects:delete_album',
                kwargs={"album_key": album.key},
            ),
            "class": "delete"
        })

    return render(request, "photo_objects/collection/show.html", {
        "collection": album,
        "photos": photos,
        "title": album.title or album.key,
        "type": "album",
        "description": meta_description(request, album),
        "back": back,
        "details": details,
        "photo": album.cover_photo,
        "info": get_info(request, album_key),
        "actions": actions,
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
        target,
        reverse(
            'photo_objects:show_album',
            kwargs={"album_key": album_key}))
    empty = album.cover_photo is None

    return render(
        request,
        'photo_objects/form.html',
        {
            "form": form,
            "title": "Edit album",
            "back": back,
            "info": get_info(
                request,
                album_key),
            "width": "narrow",
            "preview": Preview(
                request,
                album,
                preview_helptext("album", empty)),
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
            target,
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

    empty = album.cover_photo is None

    return render(request, 'photo_objects/delete.html', {
        "title": "Delete album",
        "back": back,
        "resource": target,
        "width": "narrow",
        "preview": Preview(request, album, preview_helptext("album", empty)),
        **error,
    })
