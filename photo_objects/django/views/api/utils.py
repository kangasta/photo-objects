from photo_objects.django.api.utils import JsonProblem


def json_problem_as_json(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except JsonProblem as e:
            return e.json_response
    return wrapper
