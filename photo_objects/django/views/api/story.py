from django.http import HttpRequest, HttpResponse, JsonResponse

from photo_objects.django import api
from photo_objects.django.api.utils import MethodNotAllowed

from .utils import json_problem_as_json


@json_problem_as_json
def stories(request: HttpRequest):
    if request.method == "GET":
        return get_stories(request)
    elif request.method == "POST":
        return create_story(request)
    else:
        raise MethodNotAllowed(["GET", "POST"], request.method)


def get_stories(request: HttpRequest):
    stories = api.get_stories(request)
    return JsonResponse([i.to_json() for i in stories], safe=False)


def create_story(request: HttpRequest):
    story = api.create_story(request)
    return JsonResponse(story.to_json(), status=201)


@json_problem_as_json
def story(request: HttpRequest, story_key: str):
    if request.method == "GET":
        return get_story(request, story_key)
    elif request.method == "PATCH":
        return modify_story(request, story_key)
    elif request.method == "DELETE":
        return delete_story(request, story_key)
    else:
        raise MethodNotAllowed(
            ["GET", "PATCH", "DELETE"], request.method)


def get_story(request: HttpRequest, story_key: str):
    story = api.check_story_access(request, story_key)
    return JsonResponse(story.to_json())


def modify_story(request: HttpRequest, story_key: str):
    story = api.modify_story(request, story_key)
    return JsonResponse(story.to_json())


def delete_story(request: HttpRequest, story_key: str):
    api.delete_story(request, story_key)
    return HttpResponse(status=204)
