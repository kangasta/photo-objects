from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from secrets import token_urlsafe

class Command(BaseCommand):
    help = "Create initial admin user account."

    def handle(self, *args, **options):
        User = get_user_model()
        superuser_count = User.objects.filter(is_superuser=True).count()

        if superuser_count == 0:
            username = 'admin'
            password = token_urlsafe(32)
            User.objects.create_superuser(username, password=password)

            msg = (
                self.style.SUCCESS('Initial admin account created:') +
                f'\n  Username: {username}'
                f'\n  Password: {password}'
            )

            self.stdout.write(msg)
        else:
            self.stdout.write(
                self.style.NOTICE(
                    'Initial admin account creation skipped: '
                    'Admin account(s) already exist.'
                )
            )