from photo_objects.django.api.utils import JsonProblem


def json_problem_as_html(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except JsonProblem as e:
            return e.html_response(args[0])
    return wrapper


def preview_helptext(resource_type: str, empty: bool = False) -> str:
    if resource_type == "album" and empty:
        return (
            f"This is an example on how the {resource_type} would appear "
            "when sharing on social media. Upload photos and select a cover "
            "photo to use this album specific preview instead of the server "
            "level default preview."
        )

    return (
        f"This is an example on how the {resource_type} will currently appear "
        "when sharing on social media."
    )
