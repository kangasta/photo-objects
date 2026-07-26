from uuid import UUID

from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from photo_objects.django import api
from photo_objects.django.api.utils import FormValidationFailed
from photo_objects.django.forms import ModifyPhotoReferenceForm
from photo_objects.django.views.utils import (
    BackLink,
    Preview,
)

from .utils import json_problem_as_html, preview_helptext


@json_problem_as_html
def edit_story_photo_reference(
        request: HttpRequest,
        story_key: str,
        photo_uuid: UUID):
    if request.method == "POST":
        try:
            ref = api.modify_photo_reference(request, story_key, photo_uuid)
            return HttpResponseRedirect(
                reverse(
                    'photo_objects:show_story_photo',
                    kwargs={
                        "story_key": story_key,
                        "photo_uuid": photo_uuid}))
        except FormValidationFailed as e:
            ref = api.check_photo_reference_access(
                request, story_key, photo_uuid)
            form = e.form
    else:
        ref = api.check_photo_reference_access(request, story_key, photo_uuid)
        form = ModifyPhotoReferenceForm(
            initial={
                **ref.to_json(),
            },
            instance=ref)

    target = ref.story.title or ref.story.key
    back = BackLink(
        target,
        reverse(
            'photo_objects:show_story_photo',
            kwargs={
                "story_key": story_key,
                "photo_uuid": photo_uuid}))

    return render(
        request,
        'photo_objects/form.html',
        {
            "form": form,
            "title": "Edit reference",
            "back": back,
            "width": "narrow",
            "preview": Preview(
                request,
                ref,
                preview_helptext("reference")),
        })


@json_problem_as_html
def delete_story_photo_reference(
        request: HttpRequest,
        story_key: str,
        photo_uuid: UUID):
    if request.method == "POST":
        api.delete_photo_reference(request, story_key, photo_uuid)
        return HttpResponseRedirect(
            reverse(
                'photo_objects:show_story',
                kwargs={
                    "story_key": story_key}))
    else:
        ref = api.check_photo_reference_access(request, story_key, photo_uuid)
        target = ref.story.title or ref.story.key
        back = BackLink(
            target,
            reverse(
                'photo_objects:show_story',
                kwargs={
                    "story_key": story_key}))

    return render(request, 'photo_objects/delete.html', {
        "title": "Remove from story",
        "back": back,
        "photo": ref,
        "resource": ref.title or ref.photo.filename,
        "width": "narrow",
        "preview": Preview(request, ref, preview_helptext("reference")),
    })
