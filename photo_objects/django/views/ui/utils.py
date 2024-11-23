from photo_objects.django.api.utils import JsonProblem


def json_problem_as_html(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except JsonProblem as e:
            return e.html_response(args[0])
    return wrapper
