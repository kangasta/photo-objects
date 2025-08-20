from django.http import HttpRequest, HttpResponse

from photo_objects.django import api
from photo_objects.django.api.utils import (
    JsonProblem,
)


def has_permission(request: HttpRequest):
    '''Check if user has permission to access photo in given path.

    This view is used with nginx `auth_request` directive and will thus return
    403 status code in all error situations instead of a more suitable status
    code.
    '''
    path = request.GET.get('path')
    try:
        raw_size, album_key, photo_key = path.lstrip('/').split('/')
    except (AttributeError, ValueError):
        return HttpResponse(status=403)

    try:
        api.check_photo_access(request, album_key, photo_key, raw_size)
        return HttpResponse(status=204)
    except JsonProblem:
        return HttpResponse(status=403)
