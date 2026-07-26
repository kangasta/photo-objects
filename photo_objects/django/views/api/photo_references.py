from uuid import UUID

from django.http import HttpRequest, HttpResponse, JsonResponse

from photo_objects.django import api
from photo_objects.django.api.utils import MethodNotAllowed

from .utils import json_problem_as_json


@json_problem_as_json
def story_photo_references(request: HttpRequest, story_key: str):
    if request.method == "GET":
        return get_photo_references(request, story_key)
    if request.method == "POST":
        return create_photo_reference(request, story_key)
    else:
        return MethodNotAllowed(["GET", "POST"], request.method).json_response


def get_photo_references(request: HttpRequest, story_key: str = None):
    photo_references = api.get_photo_references(request, story_key)
    return JsonResponse([i.to_json() for i in photo_references], safe=False)


def create_photo_reference(request: HttpRequest, story_key: str):
    photo_reference = api.create_photo_reference(request, story_key)
    return JsonResponse(photo_reference.to_json(), status=201)


@json_problem_as_json
def story_photo_reference(
        request: HttpRequest,
        story_key: str,
        photo_uuid: UUID):
    if request.method == "GET":
        return get_photo_reference(request, story_key, photo_uuid)
    if request.method == "PATCH":
        return modify_photo_reference(request, story_key, photo_uuid)
    if request.method == "DELETE":
        return delete_photo_reference(request, story_key, photo_uuid)
    else:
        return MethodNotAllowed(
            ["GET", "PATCH", "DELETE"], request.method).json_response


def get_photo_reference(
        request: HttpRequest,
        story_key: str,
        photo_uuid: UUID):
    ref = api.check_photo_reference_access(request, story_key, photo_uuid)
    return JsonResponse(ref.to_json())


def modify_photo_reference(
        request: HttpRequest,
        story_key: str,
        photo_uuid: UUID):
    photo_reference = api.modify_photo_reference(
        request, story_key, photo_uuid)
    return JsonResponse(photo_reference.to_json())


def delete_photo_reference(
        request: HttpRequest,
        story_key: str,
        photo_uuid: UUID):
    api.delete_photo_reference(request, story_key, photo_uuid)
    return HttpResponse(status=204)
