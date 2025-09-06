from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from photo_objects.django import api
from photo_objects.django.api.utils import (
    AlbumNotFound,
    FormValidationFailed,
    UploadPhotosFailed,
)
from photo_objects.django.forms import ModifyPhotoForm, UploadPhotosForm
from photo_objects.django.models import Photo
from photo_objects.django.views.utils import (
    BackLink,
    meta_description,
)
from photo_objects.utils import render_markdown

from .utils import json_problem_as_html


@json_problem_as_html
def upload_photos(request: HttpRequest, album_key: str):
    if request.method == "POST":
        try:
            api.upload_photos(request, album_key)
            return HttpResponseRedirect(
                reverse(
                    'photo_objects:show_album',
                    kwargs={"album_key": album_key}))
        except UploadPhotosFailed as e:
            form = e.form
            uploaded_count = len(e.uploaded_photos)
            if uploaded_count > 0:
                plural = 's' if uploaded_count != 1 else ''
                info = f"Successfully uploaded {uploaded_count} photo{plural}."
            else:
                info = None
    else:
        form = UploadPhotosForm()
        info = None

    album = api.check_album_access(request, album_key)
    target = album.title or album.key
    back = BackLink(
        f"Back to {target}", reverse(
            'photo_objects:show_album', kwargs={
                "album_key": album_key}))

    return render(request, 'photo_objects/photo/upload.html', {
        "form": form,
        "info": info,
        "title": "Upload photos",
        "back": back,
        "photo": album.cover_photo,
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


def _exposure_time_to_string(exposure_time: float | None):
    if exposure_time is None:
        return None
    if exposure_time < 1:
        return f"1/{int(1 / exposure_time)}\u202Fs"
    else:
        return f"{int(exposure_time)}\u202Fs"


def _camera_settings(photo: Photo):
    r = []
    if photo.focal_length:
        r.append(f"{round(photo.focal_length)}\u202Fmm")
    if photo.f_number:
        r.append(f"f/{photo.f_number}")
    if photo.exposure_time:
        r.append(_exposure_time_to_string(photo.exposure_time))
    if photo.iso_speed:
        r.append(f"ISO\u202F{photo.iso_speed}")
    return r


@json_problem_as_html
def show_photo(request: HttpRequest, album_key: str, photo_key: str):
    photo = api.check_photo_access(request, album_key, photo_key, "lg")

    previous_filename = photo.key.split("/")[-1]
    next_filename = previous_filename
    back = BackLink("Back to albums", reverse('photo_objects:list_albums'))

    try:
        api.check_album_access(request, photo.album.key)

        album_photos = list(
            photo.album.photo_set.values_list(
                "key", flat=True))
        photo_index = list(album_photos).index(photo.key)
        previous_filename = album_photos[(
            photo_index - 1) % len(album_photos)].split("/")[-1]
        next_filename = album_photos[(
            photo_index + 1) % len(album_photos)].split("/")[-1]

        target = photo.album.title or photo.album.key
        back = BackLink(
            f"Back to {target}", reverse(
                'photo_objects:show_album', kwargs={
                    "album_key": album_key}))
    except AlbumNotFound:
        pass

    details = {
        "Description": render_markdown(photo.description),
        "Timestamp": photo.timestamp,
        "Camera": _camera(photo),
        "Lens": _lens(photo),
        "Settings": _camera_settings(photo),
    }

    return render(request, "photo_objects/photo/show.html", {
        "photo": photo,
        "previous_filename": previous_filename,
        "next_filename": next_filename,
        "title": photo.title or photo.filename,
        "description": meta_description(request, photo),
        "back": back,
        "details": details,
    })


@json_problem_as_html
def edit_photo(request: HttpRequest, album_key: str, photo_key: str):
    if request.method == "POST":
        try:
            photo = api.modify_photo(request, album_key, photo_key)
            return HttpResponseRedirect(
                reverse(
                    'photo_objects:show_photo',
                    kwargs={
                        "album_key": album_key,
                        "photo_key": photo_key}))
        except FormValidationFailed as e:
            photo = api.check_photo_access(request, album_key, photo_key, "xs")
            form = e.form
    else:
        photo = api.check_photo_access(request, album_key, photo_key, "xs")
        form = ModifyPhotoForm(initial=photo.to_json(), instance=photo)

    target = photo.title or photo.filename
    back = BackLink(
        f'Back to {target}',
        reverse(
            'photo_objects:show_photo',
            kwargs={
                "album_key": album_key,
                "photo_key": photo_key}))

    return render(request, 'photo_objects/form.html', {
        "form": form,
        "title": "Edit photo",
        "back": back,
        "photo": photo,
    })


@json_problem_as_html
def delete_photo(request: HttpRequest, album_key: str, photo_key: str):
    if request.method == "POST":
        api.delete_photo(request, album_key, photo_key)
        return HttpResponseRedirect(
            reverse(
                'photo_objects:show_album',
                kwargs={"album_key": album_key}))
    else:
        photo = api.check_photo_access(request, album_key, photo_key, "xs")
        target = photo.title or photo.filename
        back = BackLink(
            f'Back to {target}',
            reverse(
                'photo_objects:show_photo',
                kwargs={
                    "album_key": album_key,
                    "photo_key": photo_key}))
    return render(request, 'photo_objects/delete.html', {
        "title": "Delete photo",
        "back": back,
        "photo": photo,
        "resource": target,
    })
