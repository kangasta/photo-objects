import mimetypes

from django.http import HttpRequest, HttpResponse, JsonResponse
from minio.error import S3Error
from PIL import UnidentifiedImageError

from photo_objects import Size, objsto
from photo_objects import api
from photo_objects.forms import CreatePhotoForm, ModifyPhotoForm
from photo_objects.img import photo_details, scale_photo
from photo_objects.models import Photo

from photo_objects.api.utils import (
    JsonProblem,
    MethodNotAllowed,
    check_permissions,
    parse_json_body,
    parse_single_file,
)


def photos(request: HttpRequest, album_key: str):
    if request.method == "GET":
        return get_photos(request, album_key)
    if request.method == "POST":
        return upload_photo(request, album_key)
    else:
        return MethodNotAllowed(["GET", "POST"], request.method).json_response


def get_photos(request: HttpRequest, album_key: str):
    try:
        photos = api.get_photos(request, album_key)
    except JsonProblem as e:
        return e.json_response

    return JsonResponse([i.to_json() for i in photos], safe=False)


def upload_photo(request: HttpRequest, album_key: str):
    try:
        check_permissions(
            request,
            'photo_objects.add_photo',
            'photo_objects.change_album')
        photo_file = parse_single_file(request)
    except JsonProblem as e:
        return e.json_response

    try:
        timestamp, tiny_base64 = photo_details(photo_file)
    except UnidentifiedImageError:
        return JsonProblem(
            "Could not open photo file.",
            400,
        ).json_response

    f = CreatePhotoForm(dict(
        key=photo_file.name,
        album=album_key,
        title="",
        description="",
        timestamp=timestamp,
        tiny_base64=tiny_base64,
    ))

    if not f.is_valid():
        return JsonProblem(
            "Photo validation failed.",
            400,
            errors=f.errors.get_json_data(),
        ).json_response
    photo = f.save()

    photo_file.seek(0)
    try:
        objsto.put_photo(photo.album.key, photo.key, "og", photo_file)
    except BaseException:
        # TODO: logging
        return JsonProblem(
            "Could not save photo to object storage.",
            500,
        ).json_response

    return JsonResponse(photo.to_json(), status=201)


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
    try:
        photo = api.check_photo_access(request, album_key, photo_key, 'xs')
        return JsonResponse(photo.to_json())
    except JsonProblem as e:
        return e.json_response


def modify_photo(request: HttpRequest, album_key: str, photo_key: str):
    try:
        check_permissions(request, 'photo_objects.change_photo')
        photo = api.check_photo_access(request, album_key, photo_key, 'xs')
        data = parse_json_body(request)
    except JsonProblem as e:
        return e.json_response

    f = ModifyPhotoForm({**photo.to_json(), **data}, instance=photo)
    photo = f.save()
    return JsonResponse(photo.to_json())


def delete_photo(request: HttpRequest, album_key: str, photo_key: str):
    try:
        check_permissions(request, 'photo_objects.delete_photo')
        photo = api.check_photo_access(request, album_key, photo_key, 'xs')
    except JsonProblem as e:
        return e.json_response

    try:
        objsto.delete_photo(album_key, photo_key)
    except S3Error:
        return JsonProblem(
            "Could not delete photo from object storage.",
            500,
        ).json_response

    try:
        photo.delete()
    except Exception:
        return JsonProblem(
            "Could not delete photo from database.",
            500,
        ).json_response
    return HttpResponse(status=204)


def get_img(request: HttpRequest, album_key: str, photo_key: str):
    try:
        size = request.GET.get("size")
        api.check_photo_access(request, album_key, photo_key, size)
    except JsonProblem as e:
        return e.json_response

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