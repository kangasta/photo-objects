from dataclasses import asdict
import mimetypes
from uuid import UUID

from django.http import HttpRequest, HttpResponse, JsonResponse
from minio.error import S3Error
from urllib3.exceptions import HTTPError

from photo_objects import logger
from photo_objects.django.conf import PhotoSize, photo_sizes
from photo_objects.django import api
from photo_objects.django.api.utils import (
    JsonProblem,
    MethodNotAllowed,
)
from photo_objects.django import objsto
from photo_objects.img import scale_photo

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
    photo = api.upload_photo(request, album_key)
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
    photo = api.modify_photo(request, album_key, photo_key)
    return JsonResponse(photo.to_json())


def delete_photo(request: HttpRequest, album_key: str, photo_key: str):
    api.delete_photo(request, album_key, photo_key)
    return HttpResponse(status=204)


@json_problem_as_json
def get_img(request: HttpRequest, photo_uuid: UUID):
    size = request.GET.get("size")
    photo = api.check_photo_access_by_uuid(request, photo_uuid, size)

    content_type = mimetypes.guess_type(photo.filename)[0]

    try:
        # Original photos are stored with the album key and filename, while
        # scaled photos are stored with the uuid as the filename (and _uuid
        # as the album key).
        if size == "og":
            photo_response = objsto.get_photo(
                photo.album.key, photo.filename, size)
        else:
            photo_response = objsto.get_photo("_uuid", photo_uuid, size)
        return HttpResponse(photo_response.read(), content_type=content_type)
    except S3Error:
        try:
            original_photo = objsto.get_photo(
                photo.album.key, photo.filename, PhotoSize.ORIGINAL.value)
        except (S3Error, HTTPError) as e:
            msg = objsto.with_error_code(
                "Could not fetch photo from object storage", e)
            logger.error(f"{msg}: {str(e)}")

            code = objsto.get_error_code(e)
            return JsonProblem(
                f"{msg}.",
                404 if code == "NoSuchKey" else 500,
            ).json_response

        size_params = getattr(photo_sizes(), size)
        # TODO: handle error
        scaled_photo = scale_photo(
            original_photo, photo.filename, **asdict(size_params))

        # TODO: handle error
        scaled_photo.seek(0)
        objsto.put_photo(
            "_uuid",
            str(photo_uuid),
            size,
            scaled_photo,
            size_params.image_format,
            filename=photo.filename,
        )

        content_type, headers = objsto.photo_content_headers(
            photo.filename, size_params.image_format)

        scaled_photo.seek(0)
        return HttpResponse(
            scaled_photo.read(), content_type=content_type, headers=headers)


@json_problem_as_json
def photo_change_requests(
        request: HttpRequest,
        album_key: str,
        photo_key: str):
    if request.method == "POST":
        return create_change_request(request, album_key, photo_key)
    else:
        return MethodNotAllowed(["POST"], request.method).json_response


def create_change_request(
        request: HttpRequest,
        album_key: str,
        photo_key: str):
    change_request = api.create_photo_change_request(
        request, album_key, photo_key)
    return JsonResponse(change_request.to_json(), status=201)


@json_problem_as_json
def expected_photo_change_requests(request: HttpRequest):
    if request.method != "GET":
        return MethodNotAllowed(["GET"], request.method).json_response

    return JsonResponse(
        api.get_expected_photo_change_requests(request),
        safe=False,
    )
