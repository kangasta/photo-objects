from uuid import UUID

from django.http import HttpRequest

from photo_objects.django.forms import (
    CreatePhotoReferenceForm,
    ModifyPhotoReferenceForm,)
from photo_objects.django.models import Visibility

from .auth import (
    check_photo_access_by_uuid,
    check_photo_reference_access,
    check_story_access,
)
from .utils import (
    FormValidationFailed,
    check_permissions,
    parse_input_data,
)


def get_photo_references(
        request: HttpRequest,
        story_key: str):
    story = check_story_access(request, story_key)
    refs = story.photo_references

    if not request.user.is_authenticated:
        refs = refs.filter(photo__album__visibility__in=[
            Visibility.PUBLIC,
            Visibility.HIDDEN,
        ])
    elif request.user.is_staff:
        refs = refs.all()
    else:
        refs = refs.filter(photo__album__visibility__in=[
            Visibility.PUBLIC,
            Visibility.HIDDEN,
            Visibility.PRIVATE,
        ])

    return refs.order_by("-photo__timestamp")


def create_photo_reference(
        request: HttpRequest,
        story_key: str = None,
        photo_uuid: UUID = None):
    check_permissions(request, 'photo_objects.add_photoreference')
    data = parse_input_data(request)

    if story_key:
        story = check_story_access(request, story_key)
        data = {**data, 'story': story.key}

    if photo_uuid:
        photo = check_photo_access_by_uuid(request, photo_uuid, 'xs')
        data = {**data, 'photo': photo}

    f = CreatePhotoReferenceForm(data)

    if not f.is_valid():
        raise FormValidationFailed(f)

    return f.save()


def modify_photo_reference(
        request: HttpRequest,
        story_key: str,
        photo_uuid: UUID):
    check_permissions(request, 'photo_objects.change_photoreference')
    ref = check_photo_reference_access(request, story_key, photo_uuid)

    data = parse_input_data(request)
    f = ModifyPhotoReferenceForm({**ref.to_json(), **data}, instance=ref)

    if not f.is_valid():
        raise FormValidationFailed(f)

    return f.save()


def delete_photo_reference(
        request: HttpRequest,
        story_key: str,
        photo_uuid: UUID):
    check_permissions(request, 'photo_objects.delete_photoreference')

    ref = check_photo_reference_access(request, story_key, photo_uuid)
    ref.delete()
