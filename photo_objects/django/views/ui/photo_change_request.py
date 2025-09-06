from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from photo_objects.django import api
from photo_objects.django.api.utils import (
    FormValidationFailed,
)
from photo_objects.django.forms import ReviewPhotoChangeRequestForm
from photo_objects.django.views.utils import BackLink
from photo_objects.utils import render_markdown

from .utils import json_problem_as_html


@json_problem_as_html
def next_photo_change_request(request: HttpRequest):
    change_request = api.get_next_photo_change_request(request)

    return HttpResponseRedirect(
        reverse(
            'photo_objects:review_photo_change_request',
            kwargs={"cr_id": change_request.id},
        ))


@json_problem_as_html
def review_photo_change_request(request: HttpRequest, cr_id: str):
    if request.method == "POST":
        try:
            api.review_photo_change_request(request, cr_id)
            return HttpResponseRedirect(
                reverse('photo_objects:next_photo_change_request'))
        except FormValidationFailed as e:
            _, photo = api.get_photo_change_request_and_photo(request, cr_id)
            form = e.form
    else:
        change_request, photo = api.get_photo_change_request_and_photo(
            request, cr_id)
        form = ReviewPhotoChangeRequestForm(
            initial={**change_request.to_json()},
            instance=change_request)

    count = api.get_photo_change_request_count(request)
    if count == 1:
        info = "This is the last change request in the review queue."
    else:
        info = f"There are {count} change requests in the review queue."

    back = BackLink("Back to albums", reverse('photo_objects:list_albums'))

    return render(request, 'photo_objects/form.html', {
        "form": form,
        "title": "Review photo change request",
        "back": back,
        "photo": photo,
        "info": info,
        "instructions": render_markdown(
            f'The current alt text for `{photo.key}` is: '
            f'_"{photo.alt_text}"_.'),
    })
