from django.db.models import Count
from django.http import HttpRequest

from photo_objects.django.forms import (
    CreatePhotoChangeRequestForm,
    ReviewPhotoChangeRequestForm,
)
from photo_objects.django.models import Album, Photo, PhotoChangeRequest

from .auth import check_photo_access
from .utils import (
    FormValidationFailed,
    PhotoChangeRequestNotFound,
    JsonProblem,
    check_permissions,
    parse_input_data,
)


def create_photo_change_request(
        request: HttpRequest,
        album_key: str,
        photo_key: str):
    check_permissions(request, 'photo_objects.add_photochangerequest')
    photo = check_photo_access(request, album_key, photo_key, 'xs')
    data = parse_input_data(request)

    f = CreatePhotoChangeRequestForm({**data, "photo": photo.key})

    if not f.is_valid():
        raise FormValidationFailed(f)

    change_request = f.save()
    return change_request


def get_photo_change_request_count(request: HttpRequest):
    check_permissions(
        request,
        'photo_objects.change_photo',
        'photo_objects.delete_photochangerequest')

    return PhotoChangeRequest.objects.count()


def get_next_photo_change_request(request: HttpRequest):
    check_permissions(
        request,
        'photo_objects.change_photo',
        'photo_objects.delete_photochangerequest')

    change_request = PhotoChangeRequest.objects.first()
    if not change_request:
        raise JsonProblem("No pending photo change requests.", 404) from None

    return change_request


def get_expected_photo_change_requests(request: HttpRequest):
    check_permissions(request, 'photo_objects.add_photochangerequest')

    photos = Photo.objects.filter(
        alt_text="",
    ).annotate(
        change_requests_count=Count('change_requests'),
    ).filter(
        change_requests_count=0,
    )

    if not request.user.is_staff:
        photos = photos.exclude(album__visibility=Album.Visibility.ADMIN)

    return [photo.key for photo in photos]


def get_photo_change_request_and_photo(
        request: HttpRequest,
        cr_id: int):
    try:
        change_request = PhotoChangeRequest.objects.get(id=cr_id)
    except PhotoChangeRequest.DoesNotExist:
        raise PhotoChangeRequestNotFound(cr_id) from None

    album_key = change_request.photo.album.key
    photo_key = change_request.photo.filename
    photo = check_photo_access(request, album_key, photo_key, 'xs')

    return change_request, photo


def review_photo_change_request(
        request: HttpRequest,
        cr_id: int):
    check_permissions(
        request,
        'photo_objects.change_photo',
        'photo_objects.delete_photochangerequest')

    change_request, photo = get_photo_change_request_and_photo(request, cr_id)
    data = parse_input_data(request)

    f = ReviewPhotoChangeRequestForm(data, instance=change_request)

    if not f.is_valid():
        raise FormValidationFailed(f)

    if f.cleaned_data['action'] == "approve":
        photo.alt_text = f.cleaned_data['alt_text']
        photo.save()

    f.instance.delete()
