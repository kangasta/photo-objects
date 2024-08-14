from django.http import HttpRequest, HttpResponse


def upload_photos(request: HttpRequest, album_key: str):
    return HttpResponse("upload_photos")


def show_photo(request: HttpRequest, album_key: str, photo_key: str):
    return HttpResponse("show_photo")


def edit_photo(request: HttpRequest, album_key: str, photo_key: str):
    return HttpResponse("edit_photo")


def delete_photo(request: HttpRequest, album_key: str, photo_key: str):
    return HttpResponse("delete_photo")
