from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.db import transaction

from photo_objects.django.models import Album, Backup, Photo
from photo_objects.django.objsto import (
    backup_data_key,
    backup_info_key,
    delete_backup_objects,
    get_backup_data,
    get_backup_objects,
    put_backup_json,
)
from photo_objects.utils import timestamp_str


def _permission_dict(permission: Permission):
    return {
        "app_label": permission.content_type.app_label,
        "codename": permission.codename,
    }


def _get_permissions(permissions=None):
    for permission in (permissions or []):
        yield Permission.objects.get(
            content_type__app_label=permission.get("app_label"),
            codename=permission.get("codename"))


def _user_dict(user):
    return {
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "groups": [
            i.name for i in user.groups.all()],
        "user_permissions": [
            _permission_dict(i) for i in user.user_permissions.all()],
        "is_staff": user.is_staff,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "last_login": timestamp_str(
            user.last_login),
        "date_joined": timestamp_str(
            user.date_joined)}


def _group_dict(group: Group):
    return {
        "name": group.name,
        "permissions": [_permission_dict(i) for i in group.permissions.all()],
    }


def create_backup(backup: Backup):
    user_model = get_user_model()

    backup.status = "pending"
    backup.save()

    try:
        albums = Album.objects.all()
        for album in albums:
            album_dict = album.to_json()
            photos = []
            for photo in album.photo_set.all():
                photos.append(photo.to_json())
            album_dict["photos"] = photos

            put_backup_json(
                backup_data_key(
                    backup.id,
                    'album',
                    album.key),
                album_dict,
            )

        groups = Group.objects.all()
        for group in groups:
            put_backup_json(
                backup_data_key(
                    backup.id,
                    'group',
                    group.name),
                _group_dict(group),
            )

        users = user_model.objects.all()
        for user in users:
            if user.username == "admin":
                continue

            put_backup_json(
                backup_data_key(
                    backup.id,
                    'user',
                    user.username),
                _user_dict(user))

        put_backup_json(backup_info_key(backup.id), backup.to_json())
    except Exception:
        backup.status = "create_failed"
        backup.save()

    backup.status = "ready"
    backup.save()


def delete_backup(backup: Backup):
    return delete_backup_objects(backup.id)


def get_backups() -> list[dict]:
    return get_backup_objects()


@transaction.atomic
def restore_backup(backup_id: int):
    user_model = get_user_model()

    for i in get_backups():
        Backup.objects.create(**i)

    for i in get_backup_data(backup_id, "group"):
        group = Group.objects.create(name=i.get('name'))

        for permission in _get_permissions(i.get('permissions')):
            group.permissions.add(permission)

        group.save()

    for i in get_backup_data(backup_id, "user"):
        permissions = i.pop("user_permissions")
        groups = i.pop("groups")

        user = user_model.objects.create(**i)

        for group in groups:
            user.groups.add(Group.objects.get(name=group))

        for permission in _get_permissions(permissions):
            user.user_permissions.add(permission)

        user.save()

    for i in get_backup_data(backup_id, "album"):
        photos = i.pop("photos")
        cover_photo = i.pop("cover_photo")

        album = Album.objects.create(**i)

        for photo in photos:
            photo.pop("album", None)
            filename = photo.pop("filename")

            photo = Photo.objects.create(**photo, album=album)

            if cover_photo == filename:
                album.cover_photo = photo
                album.save()
