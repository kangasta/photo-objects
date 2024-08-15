from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from photo_objects import api
from photo_objects.api.utils import FormValidationFailed
from photo_objects.forms import ModifyPhotoForm

def upload_photo(request: HttpRequest, album_key: str):
    return HttpResponse("upload_photo")


def show_photo(request: HttpRequest, album_key: str, photo_key: str):
    return HttpResponse("show_photo")


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

    return render(request, 'photo_objects/form.html', {"form": form, "title": "Edit photo"})


def delete_photo(request: HttpRequest, album_key: str, photo_key: str):
    return HttpResponse("delete_photo")
