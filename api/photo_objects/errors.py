from django.http import JsonResponse

from .constants import APPLICATION_PROBLEM

class PhotoObjectsError(Exception):
    pass


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
