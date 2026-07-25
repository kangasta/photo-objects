from django.http import HttpRequest

from photo_objects.django.forms import CreateStoryForm, ModifyStoryForm
from photo_objects.django.models import Story, Visibility

from .auth import check_story_access
from .utils import (
    FormValidationFailed,
    JsonProblem,
    check_permissions,
    parse_input_data,
)


def get_stories(request: HttpRequest):
    if not request.user.is_authenticated:
        return Story.objects.filter(visibility=Visibility.PUBLIC)
    if request.user.is_staff:
        return Story.objects.all()

    return Story.objects.filter(visibility__in=[
        Visibility.PUBLIC,
        Visibility.HIDDEN,
        Visibility.PRIVATE,
    ])


def create_story(request: HttpRequest):
    check_permissions(request, 'photo_objects.add_story')
    data = parse_input_data(request)

    f = CreateStoryForm(data, user=request.user)
    if not f.is_valid():
        raise FormValidationFailed(f)

    return f.save()


def modify_story(request: HttpRequest, story_key: str):
    check_permissions(request, 'photo_objects.change_story')
    story = check_story_access(request, story_key)
    data = parse_input_data(request)

    f = ModifyStoryForm({**story.to_json(), **data},
                        instance=story, user=request.user)
    if not f.is_valid():
        raise FormValidationFailed(f)

    return f.save()


def delete_story(request: HttpRequest, story_key: str):
    check_permissions(request, 'photo_objects.delete_story')
    story = check_story_access(request, story_key)

    if story.key.startswith('_'):
        raise JsonProblem(
            f"Story with {story_key} key is managed by the system and can not "
            "be deleted.",
            409,
        )

    story.delete()
