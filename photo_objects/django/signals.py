from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Photo


@receiver(post_save, sender=Photo)
def update_album_on_photo_upload(sender, **kwargs):
    photo = kwargs.get('instance', None)
    album = photo.album

    needs_save = False
    if album.cover_photo is None:
        needs_save = True
        album.cover_photo = photo

    if not album.first_timestamp or photo.timestamp < album.first_timestamp:
        needs_save = True
        album.first_timestamp = photo.timestamp

    if not album.last_timestamp or photo.timestamp > album.last_timestamp:
        needs_save = True
        album.last_timestamp = photo.timestamp

    if needs_save:
        album.save()


@receiver(post_delete, sender=Photo)
def update_album_on_photo_delete(sender, **kwargs):
    photo = kwargs.get('instance', None)
    album = photo.album

    try:
        first_photo = album.photo_set.latest('-timestamp')
        last_photo = album.photo_set.latest('timestamp')
    except Photo.DoesNotExist:
        album.cover_photo = None
        album.first_timestamp = None
        album.last_timestamp = None
        album.save()
        return

    needs_save = False
    if album.cover_photo is None:
        needs_save = True
        album.cover_photo = first_photo

    if album.first_timestamp < first_photo.timestamp:
        needs_save = True
        album.first_timestamp = first_photo.timestamp

    if album.last_timestamp > last_photo.timestamp:
        needs_save = True
        album.last_timestamp = last_photo.timestamp

    if needs_save:
        album.save()
