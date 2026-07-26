from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from photo_objects.django import api
from photo_objects.django.api.utils import FormValidationFailed
from photo_objects.django.forms import CreateStoryForm, ModifyStoryForm
from photo_objects.django.models import Visibility
from photo_objects.django.views.utils import (
    BackLink,
    Preview,
    meta_description,
)
from photo_objects.utils import render_markdown

from .utils import json_problem_as_html, preview_helptext


@json_problem_as_html
def list_stories(request: HttpRequest):
    stories = api.get_stories(request)
    if len(stories) == 0:
        grouped_stories = {}
    else:
        grouped_stories = {"": stories}

    actions = []
    if request.user.has_perm("photo_objects.add_story"):
        actions.append({
            "label": "New story",
            "target": reverse('photo_objects:new_story'),
        })

    return render(request, "photo_objects/collection/list.html", {
        "grouped_collections": grouped_stories,
        "title": "Stories",
        "type": "stories",
        "actions": actions,
        "show_name": "photo_objects:show_story",
    })


@json_problem_as_html
def new_story(request: HttpRequest):
    if request.method == "POST":
        try:
            story = api.create_story(request)
            return HttpResponseRedirect(
                reverse(
                    'photo_objects:show_story',
                    kwargs={
                        "story_key": story.key}))
        except FormValidationFailed as e:
            form = e.form
    else:
        form = CreateStoryForm(initial={"key": "_new"}, user=request.user)

    back = BackLink("Stories", reverse('photo_objects:list_stories'))

    return render(request, 'photo_objects/form.html', {
        "form": form,
        "title": "Create story",
        "back": back,
        "width": "narrow",
    })


@json_problem_as_html
def show_story(request: HttpRequest, story_key: str):
    story = api.check_story_access(request, story_key)
    photos = story.photo_references.all()

    back = BackLink("Stories", reverse('photo_objects:list_stories'))
    details = {
        "Description": render_markdown(story.description),
        "Visibility": Visibility(story.visibility).label,
        "Created at": story.created_at,
        "Updated at": story.updated_at,
    }

    actions = []
    if request.user.has_perm("photo_objects.change_story"):
        actions.append({
            "label": "Edit story",
            "target": reverse(
                'photo_objects:edit_story',
                kwargs={"story_key": story.key},
            ),
        })

    if request.user.has_perm("photo_objects.delete_story"):
        actions.append({
            "label": "Delete story",
            "target": reverse(
                'photo_objects:delete_story',
                kwargs={"story_key": story.key},
            ),
            "class": "delete"
        })

    return render(request, "photo_objects/collection/show.html", {
        "collection": story,
        "photos": photos,
        "title": story.title or story.key,
        "description": meta_description(request, story),
        "back": back,
        "details": details,
        "photo": story.cover_photo,
        "actions": actions,
    })


@json_problem_as_html
def edit_story(request: HttpRequest, story_key: str):
    if request.method == "POST":
        try:
            story = api.modify_story(request, story_key)
            return HttpResponseRedirect(
                reverse(
                    'photo_objects:show_story',
                    kwargs={
                        "story_key": story.key}))
        except FormValidationFailed as e:
            story = api.check_story_access(request, story_key)
            form = e.form
    else:
        story = api.check_story_access(request, story_key)
        cover_photo = story.cover_photo.id if story.cover_photo else None
        form = ModifyStoryForm(
            initial={
                **story.to_json(),
                'cover_photo': cover_photo},
            instance=story,
            user=request.user)

    target = story.title or story.key
    back = BackLink(
        target,
        reverse(
            'photo_objects:show_story',
            kwargs={"story_key": story_key}))
    empty = story.cover_photo is None

    return render(
        request,
        'photo_objects/form.html',
        {
            "form": form,
            "title": "Edit story",
            "back": back,
            "width": "narrow",
            "preview": Preview(
                request,
                story,
                preview_helptext("story", empty)),
        })


@json_problem_as_html
def delete_story(request: HttpRequest, story_key: str):
    if request.method == "POST":
        api.delete_story(request, story_key)
        return HttpResponseRedirect(reverse('photo_objects:list_stories'))
    else:
        story = api.check_story_access(request, story_key)
        target = story.title or story.key
        back = BackLink(
            target,
            reverse(
                'photo_objects:show_story',
                kwargs={
                    "story_key": story_key}))

        error = {}
        if story.photo_references.count() > 0:
            error = {'error': _(
                'Story can not be deleted because it contains photos. Delete '
                'all photos from the story to be able to delete the story.')}
        if story.key.startswith('_'):
            error = {'error': _(
                'This story is managed by the system and can not be deleted.')}

    empty = story.cover_photo is None

    return render(request, 'photo_objects/delete.html', {
        "title": "Delete story",
        "back": back,
        "photo": story.cover_photo,
        "resource": target,
        "width": "narrow",
        "preview": Preview(request, story, preview_helptext("story", empty)),
        **error,
    })
