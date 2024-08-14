import json

from django.http import HttpRequest, JsonResponse
from django.core.files.uploadedfile import UploadedFile
from django.shortcuts import render

from photo_objects.error import PhotoObjectsError
from photo_objects import Size


APPLICATION_JSON = "application/json"
MULTIPART_FORMDATA = "multipart/form-data"
APPLICATION_PROBLEM = "application/problem+json"


def _pretty_list(in_: list, conjunction: str):
    return f' {conjunction} '.join(
        i for i in (', '.join(in_[:-1]), in_[-1],) if i)


class JsonProblem(PhotoObjectsError):
    def __init__(self, title, status, payload=None, headers=None, errors=None):
        super().__init__(title)

        self.title = title
        self.status = status
        self.payload = payload or {}
        self.headers = headers
        self.errors = errors

    @property
    def json_response(self):
        payload = {
            'title': self.title,
            'status': self.status,
            **self.payload
        }

        if self.errors:
            payload['errors'] = self.errors

        return JsonResponse(
            payload,
            content_type=APPLICATION_PROBLEM,
            status=self.status,
            headers=self.headers
        )

    def html_response(self, request: HttpRequest):
        return render(request, "photo_objects/problem.html", {
            "title": self.title,
            "status": self.status
        }, status=self.status)


class MethodNotAllowed(JsonProblem):
    def __init__(self, expected: list[str], actual: str):
        expected_human = _pretty_list(expected, "or")

        super().__init__(
            f"Expected {expected_human} method, got {actual}.",
            405,
            headers=dict(Allow=', '.join(expected))
        )


class UnsupportedMediaType(JsonProblem):
    def __init__(self, expected: str, actual: str):
        super().__init__(
            f"Expected {expected} content-type, got {actual}.",
            415,
            headers=dict(Accept=expected)
        )


class Unauthorized(JsonProblem):
    def __init__(self):
        super().__init__(
            "Not authenticated.",
            401,
        )


class InvalidSize(JsonProblem):
    def __init__(self, actual: str):
        expected = _pretty_list([i.value for i in Size], "or")

        super().__init__(
            f"Expected {expected} size, got {actual or 'none'}.",
            400,
        )


class AlbumNotFound(JsonProblem):
    def __init__(self, album_key: str):
        super().__init__(
            f"Album with {album_key} key does not exist.",
            404,
        )


class PhotoNotFound(JsonProblem):
    def __init__(self, album_key: str, photo_key: str):
        super().__init__(
            f"Photo with {photo_key} key does not exist in {album_key} album.",
            404,
        )


def check_permissions(request: HttpRequest, *permissions: str):
    if not request.user.is_authenticated:
        raise Unauthorized()
    if not request.user.has_perms(permissions):
        raise JsonProblem(
            f"Expected {_pretty_list(permissions, 'and')} permissions",
            403,
            headers=dict(Allow="GET, POST")
        )


def parse_json_body(request: HttpRequest):
    if request.content_type != APPLICATION_JSON:
        raise UnsupportedMediaType(
            APPLICATION_JSON,
            request.content_type
        )

    try:
        return json.loads(request.body)
    except BaseException:
        raise JsonProblem(
            "Could not parse JSON data from request body.",
            400,
        )


def parse_single_file(request: HttpRequest) -> UploadedFile:
    if request.content_type != MULTIPART_FORMDATA:
        raise UnsupportedMediaType(
            MULTIPART_FORMDATA,
            request.content_type
        )

    if len(request.FILES) < 1:
        raise JsonProblem(
            f"Expected exactly one file, got {len(request.FILES)}.",
            400,
        )

    for _, f in request.FILES.items():
        return f
