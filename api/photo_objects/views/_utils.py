import json

from django.http import HttpRequest, JsonResponse

from photo_objects.errors import PhotoObjectsError


APPLICATION_JSON = "application/json"
APPLICATION_PROBLEM = "application/problem+json"


class JsonProblem(PhotoObjectsError):
    def __init__(self, title, status, payload=None, headers=None):
        super().__init__(title)

        self.title = title
        self.status = status
        self.payload = payload or {}
        self.headers = headers

    @property
    def json_response(self):
        payload = {
            'title': self.title,
            'status': self.status,
            **self.payload
        }

        return JsonResponse(
            payload,
            content_type=APPLICATION_PROBLEM,
            status=self.status,
            headers=self.headers
        )


class MethodNotAllowed(JsonProblem):
    def __init__(self, expected: list[str], actual: str):
        expected_human = ' or '.join(
            i for i in (', '.join(expected[:-1]), expected[-1],) if i)

        super().__init__(
            f"Expected {expected_human} method, got {actual}.",
            405,
            headers=dict(Allow=', '.join(expected))
        )


def _check_permission(request: HttpRequest, permission: str):
    if not request.user.is_authenticated:
        raise JsonProblem(
            "Not authenticated.",
            401,
        )
    if not request.user.has_perm(permission):
        raise JsonProblem(
            f"Expected {permission} permission",
            403,
            headers=dict(Allow="GET, POST")
        )


def _parse_json_body(request: HttpRequest):
    if request.content_type != APPLICATION_JSON:
        raise JsonProblem(
            f"Expected {APPLICATION_JSON} content-type, got {request.content_type}.",
            415,
            headers=dict(Accept=APPLICATION_JSON)
        )

    try:
        return json.loads(request.body)
    except:
        raise JsonProblem(
            "Could not parse JSON data from request body.",
            400,
        )
