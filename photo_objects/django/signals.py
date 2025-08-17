import re

from django.contrib.sites.models import Site
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .api.album import parse_site_id, get_site_album
from .models import Album, Photo


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


@receiver(post_save, sender=Site)
def update_album_on_site_save(sender, **kwargs):
    site = kwargs.get('instance', None)
    album, created = get_site_album(site)

    if not created and album.title != site.name:
        album.title = site.name
        album.save()


@receiver(post_save, sender=Album)
def update_site_on_album_save(sender, **kwargs):
    album = kwargs.get('instance', None)
    site_id = parse_site_id(album.key)
    if site_id is None:
        return

    try:
        site = Site.objects.get(id=site_id)
    except Site.DoesNotExist:
        return

    if site.name != album.title:
        site.name = album.title
        site.save()
