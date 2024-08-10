from django.db import models
from django.utils.translation import gettext_lazy as _


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

    def to_json(self):
        return dict(
            key=self.key,
            visibility=self.visibility,
            title=self.title,
            description=self.description,
            photos=[i.to_json() for i in self.photo_set.all()]
        )


class Photo(models.Model):
    key = models.CharField(primary_key=True)
    album = models.ForeignKey(Album, null=True, on_delete=models.SET_NULL)

    timestamp = models.DateTimeField()
    title = models.CharField(blank=True)
    description = models.TextField(blank=True)

    tiny_base64 = models.TextField(blank=True)

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
