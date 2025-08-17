from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site

from photo_objects.django.api.album import get_site_album
from photo_objects.django.models import Album


class Command(BaseCommand):
    help = "Create albums for configuring site metadata."

    def handle(self, *args, **options):
        sites = Site.objects.all()

        for site in sites:
            album, created = get_site_album(site)
            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Album for site {site.domain} created:') +
                    f'\n  Key: {album.key}'
                    f'\n  Title: {album.title}')
            else:
                self.stdout.write(
                    self.style.NOTICE(
                        f'Album creation for site {site.domain} skipped: '
                        'Album already exists.'
                    )
                )
