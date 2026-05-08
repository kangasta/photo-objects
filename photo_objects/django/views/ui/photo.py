from uuid import UUID

from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.safestring import mark_safe

from photo_objects.django import api
from photo_objects.django.api.utils import (
    AlbumNotFound,
    FormValidationFailed,
)
from photo_objects.django.forms import ModifyPhotoForm
from photo_objects.django.models import Photo, SiteSettings
from photo_objects.django.views.utils import (
    BackLink,
    Preview,
    meta_description,
)
from photo_objects.utils import render_markdown

from .utils import json_problem_as_html, preview_helptext, year_month


@json_problem_as_html
def upload_photos(request: HttpRequest, album_key: str):
    album = api.check_album_access(request, album_key)
    target = album.title or album.key
    back = BackLink(
        target, reverse(
            'photo_objects:show_album', kwargs={
                "album_key": album_key}))
    empty = album.cover_photo is None

    return render(request, 'photo_objects/photo/upload.html', {
        "title": "Upload photos",
        "back": back,
        "album": album,
        "photo": album.cover_photo,
        "width": "narrow",
        "preview": Preview(request, album, preview_helptext("album", empty)),
    })


def _group_photos(
    photos: list[Photo],
    group_by: str,
) -> dict[str, list[Photo]]:
    if len(photos) == 0:
        return {}

    if group_by == "year":
        result = {}
        for photo in photos:
            key = str(
                photo.timestamp.year) if photo.timestamp else ""
            result.setdefault(key, []).append(photo)
        return result
    if group_by == "month":
        result = {}
        for photo in photos:
            if photo.timestamp is None:
                key = ""
            else:
                key = year_month(photo.timestamp)
            result.setdefault(key, []).append(photo)
        return result
    else:
        return {"": photos}


@json_problem_as_html
def list_photos(request: HttpRequest):
    try:
        settings = SiteSettings.objects.get(request.site)
        group_by = settings.photos_group_by
    except SiteSettings.DoesNotExist:
        group_by = "none"

    photos = api.get_photos(request)

    return render(request, "photo_objects/photo/list.html", {
        "grouped_photos": _group_photos(photos, group_by),
        "title": "Photos",
        "description": meta_description(request, photos),
    })


def _lower(value: str):
    return value.lower() if value else ''


def _camera(photo: Photo):
    if not photo.camera_make and not photo.camera_model:
        return None

    # If camera model includes camera make, return model value to avoid
    # stuttering.
    if _lower(photo.camera_make) in _lower(photo.camera_model):
        return photo.camera_model

    return " ".join(i for i in [
        photo.camera_make,
        photo.camera_model,
    ] if i)


def _lens(photo: Photo):
    if photo.lens_make or photo.lens_model:
        return " ".join(i for i in [photo.lens_make, photo.lens_model] if i)
    return None


def _sec(text: str):
    return f'<span class="secondary">{text}</span>'


def _exposure_time_to_string(exposure_time: float | None):
    if exposure_time is None:
        return None
    if exposure_time < 1:
        return mark_safe(
            f"{_sec('1/')}{int(1 / exposure_time)}\u202F{_sec('s')}")
    else:
        return mark_safe(
            f"{int(exposure_time)}\u202F{_sec('s')}")


def _camera_settings(photo: Photo):
    r = []
    if photo.focal_length:
        r.append(mark_safe(
            f"{round(photo.focal_length)}\u202F{_sec('mm')}"))
    if photo.f_number:
        r.append(
            mark_safe(f"{_sec('f/')}{photo.f_number}"))
    if photo.exposure_time:
        r.append(_exposure_time_to_string(photo.exposure_time))
    if photo.iso_speed:
        r.append(mark_safe(
            f"{_sec('ISO')}\u202F{photo.iso_speed}"))
    return r


def _show_photo(
        request: HttpRequest,
        photo: Photo,
        previous_path: str,
        next_path: str,
        back: BackLink):
    details = {
        "Description": render_markdown(photo.description),
        "Timestamp": photo.timestamp,
        "Camera": _camera(photo),
        "Lens": _lens(photo),
        "Settings": _camera_settings(photo),
        "Created at": photo.created_at,
        "Updated at": photo.updated_at,
    }

    return render(request, "photo_objects/photo/show.html", {
        "photo": photo,
        "previous_path": previous_path,
        "next_path": next_path,
        "title": photo.title or photo.filename,
        "description": meta_description(request, photo),
        "back": back,
        "details": details,
    })


@json_problem_as_html
def show_album_photo(request: HttpRequest, album_key: str, photo_key: str):
    photo = api.check_photo_access(request, album_key, photo_key, "lg")

    previous_filename = photo.key.split("/")[-1]
    next_filename = previous_filename
    back = BackLink("Albums", reverse('photo_objects:list_albums'))

    try:
        api.check_album_access(request, photo.album.key)

        previous_filename = photo.previous(photo.album.photo_set).filename
        next_filename = photo.next(photo.album.photo_set).filename

        target = photo.album.title or photo.album.key
        back = BackLink(
            target, reverse(
                'photo_objects:show_album', kwargs={
                    "album_key": album_key}))
    except AlbumNotFound:
        pass

    previous_path = reverse(
        'photo_objects:show_album_photo',
        kwargs={
            "album_key": album_key,
            "photo_key": previous_filename})
    next_path = reverse(
        'photo_objects:show_album_photo',
        kwargs={
            "album_key": album_key,
            "photo_key": next_filename})

    return _show_photo(request, photo, previous_path, next_path, back)


@json_problem_as_html
def show_photo(request: HttpRequest, photo_uuid: UUID):
    photo = api.check_photo_access_by_uuid(request, photo_uuid, "lg")

    previous_uuid = photo.key.split("/")[-1]
    next_uuid = previous_uuid
    back = BackLink("Photos", reverse('photo_objects:list_photos'))

    photos = api.get_photos(request)
    if len(photos) > 0:
        # The next and previous functions use oldest first sorting. The photos
        # list is sorted in opposite order, so previous is next and next is
        # previous.
        next_uuid = photo.previous(photos).uuid
        previous_uuid = photo.next(photos).uuid

    previous_path = reverse(
        'photo_objects:show_photo',
        kwargs={
            "photo_uuid": previous_uuid})
    next_path = reverse(
        'photo_objects:show_photo',
        kwargs={
            "photo_uuid": next_uuid})

    return _show_photo(request, photo, previous_path, next_path, back)


@json_problem_as_html
def edit_album_photo(
        request: HttpRequest,
        album_key: str,
        photo_key: str,
        back_path: str = None,
        next_path: str = None):
    if request.method == "POST":
        try:
            photo = api.modify_photo(request, album_key, photo_key)
            if not next_path:
                next_path = reverse(
                    'photo_objects:show_album_photo',
                    kwargs={
                        "album_key": album_key,
                        "photo_key": photo_key})
            return HttpResponseRedirect(next_path)
        except FormValidationFailed as e:
            photo = api.check_photo_access(request, album_key, photo_key, "xs")
            form = e.form
    else:
        photo = api.check_photo_access(request, album_key, photo_key, "xs")
        form = ModifyPhotoForm(initial=photo.to_json(), instance=photo)

    target = photo.title or photo.filename
    if not back_path:
        back_path = reverse(
            'photo_objects:show_album_photo',
            kwargs={
                "album_key": album_key,
                "photo_key": photo_key})
    back = BackLink(target, back_path)

    return render(
        request,
        'photo_objects/form.html',
        {
            "form": form,
            "title": "Edit photo",
            "back": back,
            "width": "narrow",
            "preview": Preview(request, photo, preview_helptext("photo")),
        })


@json_problem_as_html
def edit_photo(request: HttpRequest, photo_uuid: UUID):
    back_path = next_path = reverse(
        'photo_objects:show_photo',
        kwargs={
            "photo_uuid": photo_uuid})

    photo = api.check_photo_access_by_uuid(request, photo_uuid, "xs")
    return edit_album_photo(
        request,
        photo.album.key,
        photo.filename,
        back_path,
        next_path)


@json_problem_as_html
def delete_album_photo(
        request: HttpRequest,
        album_key: str,
        photo_key: str,
        back_path: str = None,
        next_path: str = None):
    if request.method == "POST":
        api.delete_photo(request, album_key, photo_key)
        if not next_path:
            next_path = reverse(
                'photo_objects:show_album',
                kwargs={"album_key": album_key})
        return HttpResponseRedirect(next_path)
    else:
        photo = api.check_photo_access(request, album_key, photo_key, "xs")
        target = photo.title or photo.filename
        if not back_path:
            back_path = reverse(
                'photo_objects:show_album_photo',
                kwargs={
                    "album_key": album_key,
                    "photo_key": photo_key})
        back = BackLink(target, back_path)
    return render(request, 'photo_objects/delete.html', {
        "title": "Delete photo",
        "back": back,
        "photo": photo,
        "resource": target,
        "width": "narrow",
        "preview": Preview(request, photo, preview_helptext("photo")),
    })


@json_problem_as_html
def delete_photo(request: HttpRequest, photo_uuid: UUID):
    back_path = reverse(
        'photo_objects:show_photo',
        kwargs={
            "photo_uuid": photo_uuid})
    next_path = reverse('photo_objects:list_photos')

    photo = api.check_photo_access_by_uuid(request, photo_uuid, "xs")
    return delete_album_photo(
        request,
        photo.album.key,
        photo.filename,
        back_path,
        next_path)
