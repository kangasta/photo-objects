# pylint: disable=invalid-name
from secrets import token_urlsafe

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from photo_objects.config import write_to_home_directory


class Command(BaseCommand):
    help = "Create initial admin user account."

    def handle(self, *args, **options):
        user = get_user_model()
        superuser_count = user.objects.filter(is_superuser=True).count()

        if superuser_count == 0:
            username = 'admin'
            password = token_urlsafe(32)
            user.objects.create_superuser(username, password=password)

            write_to_home_directory("initial_admin_password", password)

            self.stdout.write(
                self.style.SUCCESS('Initial admin account created:') +
                f'\n  Username: {username}'
                f'\n  Password: {password}'
            )
        else:
            self.stdout.write(
                self.style.NOTICE(
                    'Initial admin account creation skipped: '
                    'Admin account(s) already exist.'
                )
            )
