import mimetypes

from django.http import HttpRequest, HttpResponse, JsonResponse
from minio.error import S3Error

from photo_objects import Size
from photo_objects.img import photo_details, scale_photo
from photo_objects.models import Album, Photo
from photo_objects import objsto

from .auth import _check_album_access, _check_photo_access
from ._utils import (
    AlbumNotFound,
    Conflict,
    JsonProblem,
    MethodNotAllowed,
    _check_permissions,
    _parse_single_file,
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
        _check_album_access(request, album_key)
    except JsonProblem as e:
        return e.json_response

    photos = Photo.objects.filter(album__key=album_key)
    return JsonResponse([i.to_json() for i in photos], safe=False)


def upload_photo(request: HttpRequest, album_key: str):
    try:
        _check_permissions(
            request,
            'photo_objects.add_photo',
            'photo_objects.change_album')
        photo_file = _parse_single_file(request)
    except JsonProblem as e:
        return e.json_response

    try:
        album = Album.objects.get(key=album_key)
    except Album.DoesNotExist:
        return AlbumNotFound(album_key).json_response

    key = photo_file.name
    if Photo.objects.filter(key=key).exists():
        return Conflict(
            f"Photo with {key} key already exists in {album_key} album.",
        ).json_response

    timestamp, tiny_base64 = photo_details(photo_file)

    photo = Photo.objects.create(
        key=key,
        album=album,
        title="",
        description="",
        timestamp=timestamp,
        tiny_base64=tiny_base64,
    )

    photo_file.seek(0)
    try:
        objsto.put_photo(album.key, photo.key, "og", photo_file)
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
    else:
        return MethodNotAllowed(["GET"], request.method).json_response


def get_photo(request: HttpRequest, album_key: str, photo_key: str):
    try:
        photo = _check_photo_access(request, album_key, photo_key, 'xs')
        return JsonResponse(photo.to_json())
    except JsonProblem as e:
        return e.json_response


def get_img(request: HttpRequest, album_key: str, photo_key: str):
    try:
        size = request.GET.get("size")
        _check_photo_access(request, album_key, photo_key, size)
    except JsonProblem as e:
        return e.json_response

    content_type = mimetypes.guess_type(photo_key)[0]

    try:
        photo_response = objsto.get_photo(album_key, photo_key, size)
        return HttpResponse(photo_response.read(), content_type=content_type)
    except S3Error:
        original_photo = objsto.get_photo(
            album_key, photo_key, Size.ORIGINAL.value)

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
