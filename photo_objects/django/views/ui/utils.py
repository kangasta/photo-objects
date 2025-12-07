from photo_objects.django.api.utils import JsonProblem


def json_problem_as_html(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except JsonProblem as e:
            return e.html_response(args[0])
    return wrapper


def preview_helptext(resource_type: str) -> str:
    return (
        f"This is an example on how the {resource_type} will currently appear "
        "when sharing on social media."
    )
