import json

from django.forms import ModelForm
from django.http import HttpRequest, JsonResponse
from django.core.files.uploadedfile import UploadedFile
from django.shortcuts import render
from django.urls import reverse_lazy

from photo_objects.error import PhotoObjectsError
from photo_objects.utils import pretty_list
from photo_objects.django.views.utils import BackLink
from photo_objects.django.conf import PhotoSize


APPLICATION_JSON = "application/json"
APPLICATION_X_WWW_FORM = "application/x-www-form-urlencoded"
MULTIPART_FORMDATA = "multipart/form-data"
APPLICATION_PROBLEM = "application/problem+json"


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
            "title": "Error",
            "back": BackLink(
                'Back to albums',
                reverse_lazy('photo_objects:list_albums')),
            "problem_title": self.title,
            "status": self.status
        }, status=self.status)


class MethodNotAllowed(JsonProblem):
    def __init__(self, expected: list[str], actual: str):
        expected_human = pretty_list(expected, "or")

        super().__init__(
            f"Expected {expected_human} method, got {actual}.",
            405,
            headers=dict(Allow=', '.join(expected))
        )


class UnsupportedMediaType(JsonProblem):
    def __init__(self, expected: list[str], actual: str):
        expected_human = pretty_list(expected, "or")

        super().__init__(
            f"Expected {expected_human} content-type, got {actual}.",
            415,
            headers={'Accept-Post': ', '.join(expected)}
        )


class Unauthorized(JsonProblem):
    def __init__(self):
        super().__init__(
            "Not authenticated.",
            401,
        )


class InvalidSize(JsonProblem):
    def __init__(self, actual: str):
        expected = pretty_list([i.value for i in PhotoSize], "or")

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


class PhotoChangeRequestNotFound(JsonProblem):
    def __init__(self, id_: int):
        super().__init__(
            f"Photo change request with id {id_} does not exist.",
            404,
        )


class FormValidationFailed(JsonProblem):
    def __init__(self, form: ModelForm):
        try:
            resource = form.instance.__class__.__name__
        except AttributeError:
            resource = "Form"

        super().__init__(
            f"{resource} validation failed.",
            400,
            errors=form.errors.get_json_data(),
        )

        self.form = form


class UploadPhotosFailed(FormValidationFailed):
    def __init__(self, form: ModelForm, uploaded_photos: list[str]):
        super().__init__(form)
        self.uploaded_photos = uploaded_photos


def check_permissions(request: HttpRequest, *permissions: str):
    if not request.user.is_authenticated:
        raise Unauthorized()
    if not request.user.has_perms(permissions):
        raise JsonProblem(
            f"Expected {pretty_list(permissions, 'and')} permissions",
            403,
            headers=dict(Allow="GET, POST")
        )


def parse_json_body(request: HttpRequest):
    if request.content_type != APPLICATION_JSON:
        raise UnsupportedMediaType(
            [APPLICATION_JSON],
            request.content_type
        )

    try:
        return json.loads(request.body)
    except BaseException:
        raise JsonProblem(
            "Could not parse JSON data from request body.",
            400,
        ) from None


def parse_input_data(request: HttpRequest):
    if request.content_type == APPLICATION_JSON:
        return parse_json_body(request)
    elif request.content_type == APPLICATION_X_WWW_FORM:
        return request.POST.dict()
    else:
        raise UnsupportedMediaType(
            [APPLICATION_JSON, APPLICATION_X_WWW_FORM], request.content_type)


def parse_single_file(request: HttpRequest) -> UploadedFile:
    if request.content_type != MULTIPART_FORMDATA:
        raise UnsupportedMediaType(
            [MULTIPART_FORMDATA],
            request.content_type
        )

    if len(request.FILES) != 1:
        raise JsonProblem(
            f"Expected exactly one file, got {len(request.FILES)}.",
            400,
        )

    for _, f in request.FILES.items():
        return f


def join_key(*args):
    return '/'.join(args)
