# pylint: disable=invalid-name
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from photo_objects.django.api.backup import get_backups, restore_backup
from photo_objects.django.models import Album, Photo


class DatabaseStatus:
    def __init__(self):
        user = get_user_model()

        self._users = user.objects.count()
        self._groups = Group.objects.count()
        self._albums = Album.objects.count()
        self._photos = Photo.objects.count()

    def should_restore(self):
        count = self._users + self._groups + self._albums + self._photos
        return count == 0

    def __str__(self):
        return (
            f"Database contains {self._users} users, "
            f"{self._groups} groups, {self._albums} albums, and "
            f"{self._photos} photos"
        )


class Command(BaseCommand):
    help = "Restore latest backup if database is empty."

    def handle(self, *args, **options):
        status = DatabaseStatus()
        if not status.should_restore():
            self.stdout.write(
                self.style.NOTICE(
                    f'Restoring backup skipped: {status}'
                )
            )
            return

        backups = get_backups()

        if not backups:
            self.stdout.write(
                self.style.NOTICE(
                    f'Restoring backup skipped: No backups found.'
                )
            )
            return

        try:
            id_ = backups[-1].get("id")
            self.stdout.write(
                self.style.NOTICE(
                    f'Restoring backup with ID {id_}.'
                )
            )
            restore_backup(id_)
            status = DatabaseStatus()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Restored backup with ID {id_}: {status}'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'Failed to restore backup: {e}'
                )
            )
            exit(1)
