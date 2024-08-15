import mimetypes

from django.http import HttpRequest, HttpResponse, JsonResponse
from minio.error import S3Error
from PIL import UnidentifiedImageError

from photo_objects import Size, objsto
from photo_objects import api
from photo_objects.api.utils import (
    JsonProblem,
    MethodNotAllowed,
    check_permissions,
    parse_json_body,
    parse_single_file,
)
from photo_objects.forms import CreatePhotoForm, ModifyPhotoForm
from photo_objects.img import photo_details, scale_photo

from .utils import json_problem_as_json


@json_problem_as_json
def photos(request: HttpRequest, album_key: str):
    if request.method == "GET":
        return get_photos(request, album_key)
    if request.method == "POST":
        return upload_photo(request, album_key)
    else:
        return MethodNotAllowed(["GET", "POST"], request.method).json_response


def get_photos(request: HttpRequest, album_key: str):
    photos = api.get_photos(request, album_key)
    return JsonResponse([i.to_json() for i in photos], safe=False)


def upload_photo(request: HttpRequest, album_key: str):
    check_permissions(
        request,
        'photo_objects.add_photo',
        'photo_objects.change_album')
    photo_file = parse_single_file(request)

    try:
        timestamp, tiny_base64 = photo_details(photo_file)
    except UnidentifiedImageError:
        raise JsonProblem(
            "Could not open photo file.",
            400,
        )

    f = CreatePhotoForm(dict(
        key=photo_file.name,
        album=album_key,
        title="",
        description="",
        timestamp=timestamp,
        tiny_base64=tiny_base64,
    ))

    if not f.is_valid():
        raise JsonProblem(
            "Photo validation failed.",
            400,
            errors=f.errors.get_json_data(),
        )
    photo = f.save()

    photo_file.seek(0)
    try:
        objsto.put_photo(photo.album.key, photo.key, "og", photo_file)
    except BaseException:
        # TODO: logging
        raise JsonProblem(
            "Could not save photo to object storage.",
            500,
        )

    return JsonResponse(photo.to_json(), status=201)


@json_problem_as_json
def photo(request: HttpRequest, album_key: str, photo_key: str):
    if request.method == "GET":
        return get_photo(request, album_key, photo_key)
    if request.method == "PATCH":
        return modify_photo(request, album_key, photo_key)
    if request.method == "DELETE":
        return delete_photo(request, album_key, photo_key)
    else:
        return MethodNotAllowed(
            ["GET", "PATCH", "DELETE"], request.method).json_response


def get_photo(request: HttpRequest, album_key: str, photo_key: str):
    photo = api.check_photo_access(request, album_key, photo_key, 'xs')
    return JsonResponse(photo.to_json())


def modify_photo(request: HttpRequest, album_key: str, photo_key: str):
    check_permissions(request, 'photo_objects.change_photo')
    photo = api.check_photo_access(request, album_key, photo_key, 'xs')
    data = parse_json_body(request)

    f = ModifyPhotoForm({**photo.to_json(), **data}, instance=photo)
    photo = f.save()
    return JsonResponse(photo.to_json())


def delete_photo(request: HttpRequest, album_key: str, photo_key: str):
    check_permissions(request, 'photo_objects.delete_photo')
    photo = api.check_photo_access(request, album_key, photo_key, 'xs')

    try:
        objsto.delete_photo(album_key, photo_key)
    except S3Error:
        raise JsonProblem(
            "Could not delete photo from object storage.",
            500,
        )

    try:
        photo.delete()
    except Exception:
        raise JsonProblem(
            "Could not delete photo from database.",
            500,
        )
    return HttpResponse(status=204)


@json_problem_as_json
def get_img(request: HttpRequest, album_key: str, photo_key: str):
    size = request.GET.get("size")
    api.check_photo_access(request, album_key, photo_key, size)

    content_type = mimetypes.guess_type(photo_key)[0]

    try:
        photo_response = objsto.get_photo(album_key, photo_key, size)
        return HttpResponse(photo_response.read(), content_type=content_type)
    except S3Error:
        try:
            original_photo = objsto.get_photo(
                album_key, photo_key, Size.ORIGINAL.value)
        except S3Error as e:
            # TODO logging
            return JsonProblem(
                f"Could not fetch photo from object storage ({e.code}).",
                404 if e.code == "NoSuchKey" else 500,
            ).json_response

        # TODO: make configurable
        sizes = dict(sm=(None, 256), md=(1024, 1024),
                     lg=(2048, 2048), xl=(4096, 4096))
        # TODO: handle error
        scaled_photo = scale_photo(original_photo, photo_key, *sizes[size])

        # TODO: handle error
        scaled_photo.seek(0)
        objsto.put_photo(album_key, photo_key, size, scaled_photo)

        scaled_photo.seek(0)
        return HttpResponse(scaled_photo.read(), content_type=content_type)
