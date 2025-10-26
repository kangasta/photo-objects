from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission

from photo_objects.django.models import Album, Backup
from photo_objects.django.objsto import put_backup_json
from photo_objects.utils import slugify, timestamp_str


def _info_key(id_):
    return f'info_{id_}.json'


def _data_key(id_, type_, key):
    return f'data_{id_}/{type_}_{slugify(key)}.json'


def _permission_dict(permission: Permission):
    return {
        "app_label": permission.content_type.app_label,
        "codename": permission.codename,
    }


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

    albums = Album.objects.all()
    for album in albums:
        album_dict = album.to_json()
        photos = []
        for photo in album.photo_set.all():
            photos.append(photo.to_json())
        album_dict["photos"] = photos

        put_backup_json(_data_key(backup.id, 'album', album.key), album_dict,)

    groups = Group.objects.all()
    for group in groups:
        put_backup_json(
            _data_key(backup.id, 'group', group.name), _group_dict(group),)

    users = user_model.objects.all()
    for user in users:
        if user.username == "admin":
            continue

        put_backup_json(
            _data_key(backup.id, 'user', user.username), _user_dict(user))

    put_backup_json(_info_key(backup.id), backup.to_json())

    backup.status = "ready"
    backup.save()
