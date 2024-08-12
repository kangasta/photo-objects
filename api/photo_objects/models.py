from django.db import models
from django.utils.translation import gettext_lazy as _


def _str(key, **kwargs):
    details = ', '.join(f'{k}={v}' for k, v in kwargs.items() if k and v)
    return f'{key} ({details})' if details else key


class Album(models.Model):
    class Visibility(models.TextChoices):
        PUBLIC = "public", _("Public")
        HIDDEN = "hidden", _("Hidden")
        PRIVATE = "private", _("Private")

    key = models.CharField(primary_key=True)
    visibility = models.CharField(
        default=Visibility.PRIVATE,
        choices=Visibility)

    title = models.CharField(blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return _str(self.key, title=self.title, visibility=self.visibility)

    def to_json(self):
        return dict(
            key=self.key,
            visibility=self.visibility,
            title=self.title,
            description=self.description,
        )


class Photo(models.Model):
    key = models.CharField(primary_key=True)
    album = models.ForeignKey(Album, null=True, on_delete=models.PROTECT)

    timestamp = models.DateTimeField()
    title = models.CharField(blank=True)
    description = models.TextField(blank=True)

    tiny_base64 = models.TextField(blank=True)

    def __str__(self):
        return _str(
            self.key,
            album=self.album.key,
            title=self.title,
            timestamp=self.timestamp.isoformat()
        )

    def to_json(self):
        album_key = self.album.key if self.album else None

        return dict(
            key=self.key,
            album=album_key,
            timestamp=self.timestamp.isoformat(),
            tiny_base64=self.tiny_base64,
            title=self.title,
            description=self.description,
        )
