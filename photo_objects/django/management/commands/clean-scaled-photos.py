from django.core.management.base import BaseCommand

from photo_objects.utils import pretty_list
from photo_objects.django.conf import photo_sizes, CONFIGURABLE_PHOTO_SIZES
from photo_objects.django.objsto import (
    delete_scaled_photos,
    get_photo_sizes,
    put_photo_sizes,
)


class Command(BaseCommand):
    help = "Remove scaled photos when scaling settings have changed."

    def handle(self, *args, **options):
        current = photo_sizes()
        previous = get_photo_sizes()

        if current == previous:
            self.stdout.write(
                self.style.SUCCESS(
                    "No changes in photo sizes configuration."
                )
            )
            return

        if previous is None:
            self.stdout.write(
                self.style.WARNING(
                    "No previous photo sizes configuration found. "
                    "Removing all scaled photos:"
                )
            )
            to_delete = CONFIGURABLE_PHOTO_SIZES
        else:
            to_delete = []
            for size in CONFIGURABLE_PHOTO_SIZES:
                if getattr(previous, size) != getattr(current, size):
                    to_delete.append(size)

            changed = pretty_list(to_delete, 'and')
            self.stdout.write(
                self.style.NOTICE(
                    "Found changes in photo sizes configuration for "
                    f"{changed} sizes. Deleting scaled photos:"
                )
            )

        try:
            deleted_keys = delete_scaled_photos(to_delete)

            total = 0
            for key in deleted_keys:
                self.stdout.write(f"  {key}")
                total += 1
            self.stdout.write(f"  Total deleted photos: {total}")
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f"Error occurred while deleting scaled photos: {e}"
                )
            )
            return

        put_photo_sizes(current)
