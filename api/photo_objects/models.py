from django.db import models
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _


album_key_validator = RegexValidator(
    r"^[a-zA-Z0-9._-]+$",
    "Album key must only contain alphanumeric characters, dots, underscores "
    "and hyphens.")
photo_key_validator = RegexValidator(
    r"^[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+$",
    "Photo key must contain album key and filename. These must be separated "
    "with slash. Both parts must only contain alphanumeric characters, dots, "
    "underscores and hyphens.")


def _str(key, **kwargs):
    details = ', '.join(f'{k}={v}' for k, v in kwargs.items() if k and v)
    return f'{key} ({details})' if details else key


def _timestamp_str(timestamp):
    return timestamp.isoformat() if timestamp else None


class Album(models.Model):
    class Meta:
        ordering = ["-first_timestamp", "-last_timestamp", "key"]

    class Visibility(models.TextChoices):
        PUBLIC = "public", _("Public")
        HIDDEN = "hidden", _("Hidden")
        PRIVATE = "private", _("Private")

    key = models.CharField(primary_key=True, validators=[album_key_validator])
    visibility = models.CharField(
        blank=True,
        db_default=Visibility.PRIVATE,
        default=Visibility.PRIVATE,
        choices=Visibility)

    title = models.CharField(blank=True)
    description = models.TextField(blank=True)

    cover_photo = models.ForeignKey(
        "Photo",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="+")
    first_timestamp = models.DateTimeField(null=True)
    last_timestamp = models.DateTimeField(null=True)

    def __str__(self):
        return _str(self.key, title=self.title, visibility=self.visibility)

    def to_json(self):
        return dict(
            key=self.key,
            visibility=self.visibility,
            title=self.title,
            description=self.description,
            cover_photo=(
                self.cover_photo.filename if self.cover_photo else None),
            first_timestamp=_timestamp_str(self.first_timestamp),
            last_timestamp=_timestamp_str(self.last_timestamp),
        )


class Photo(models.Model):
    class Meta:
        ordering = ["timestamp"]

    key = models.CharField(primary_key=True, validators=[photo_key_validator])
    album = models.ForeignKey("Album", null=True, on_delete=models.PROTECT)

    timestamp = models.DateTimeField()
    title = models.CharField(blank=True)
    description = models.TextField(blank=True)

    tiny_base64 = models.TextField(blank=True)

    def __str__(self):
        return _str(
            self.key,
            title=self.title,
            timestamp=self.timestamp.isoformat()
        )

    @property
    def filename(self):
        return self.key.split('/')[-1]

    def to_json(self):
        album_key = self.album.key if self.album else None

        return dict(
            key=self.key,
            filename=self.filename,
            album=album_key,
            timestamp=self.timestamp.isoformat(),
            tiny_base64=self.tiny_base64,
            title=self.title,
            description=self.description,
        )
