from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Photo


@receiver(post_save, sender=Photo)
def update_album(sender, **kwargs):
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
