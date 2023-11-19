from django.contrib.auth.models import Group
from django.db import models

class Album(models.Model):
    key = models.CharField(primary_key=True)
    public = models.BooleanField(default=False)

    title = models.CharField(blank=True)
    description = models.TextField(blank=True)

    def to_json(self):
        return dict(
            key=self.key,
            public=self.public,
            title=self.title,
            description=self.description,
            photos=[i.to_json() for i in self.photo_set.exclude(tiny_base64="")]
        )


class Photo(models.Model):
    key = models.CharField(primary_key=True)
    album = models.ForeignKey(Album, null=True, on_delete=models.SET_NULL)

    timestamp = models.DateTimeField()
    title = models.CharField(blank=True)
    description = models.TextField(blank=True)

    tiny_base64 = models.CharField(blank=True)

    def to_json(self):
        album_key = self.album.key if self.album else None

        return dict(
            key=self.key,
            album=album_key,
            timestamp=f'{self.timestamp.isoformat()}Z',
            title=self.title,
            description=self.description,
        )
