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


class BaseModel(models.Model):
    title = models.CharField(blank=True)
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def to_json(self):
        return dict(
            title=self.title,
            description=self.description,
            created_at=_timestamp_str(self.created_at),
            updated_at=_timestamp_str(self.updated_at),
        )


class Album(BaseModel):
    class Meta:
        ordering = ["-first_timestamp", "-last_timestamp", "key"]

    class Visibility(models.TextChoices):
        PUBLIC = "public", _("Public")
        HIDDEN = "hidden", _("Hidden")
        PRIVATE = "private", _("Private")
        ADMIN = "", _("Admin")

    key = models.CharField(primary_key=True, validators=[album_key_validator])
    visibility = models.CharField(
        blank=True,
        db_default=Visibility.PRIVATE,
        default=Visibility.PRIVATE,
        choices=Visibility)

    cover_photo = models.ForeignKey(
        "Photo",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="+")
    first_timestamp = models.DateTimeField(blank=True, null=True)
    last_timestamp = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return _str(self.key, title=self.title, visibility=self.visibility)

    def to_json(self):
        return dict(
            **super().to_json(),
            key=self.key,
            visibility=self.visibility,
            cover_photo=(
                self.cover_photo.filename if self.cover_photo else None),
            first_timestamp=_timestamp_str(self.first_timestamp),
            last_timestamp=_timestamp_str(self.last_timestamp),
        )


class Photo(BaseModel):
    class Meta:
        ordering = ["timestamp"]

    key = models.CharField(primary_key=True, validators=[photo_key_validator])
    album = models.ForeignKey("Album", null=True, on_delete=models.PROTECT)

    timestamp = models.DateTimeField()

    height = models.PositiveIntegerField()
    width = models.PositiveIntegerField()
    tiny_base64 = models.TextField(blank=True)

    camera_make = models.CharField(blank=True)
    camera_model = models.CharField(blank=True)
    lens_make = models.CharField(blank=True)
    lens_model = models.CharField(blank=True)

    focal_length = models.FloatField(blank=True, null=True)
    f_number = models.FloatField(blank=True, null=True)
    exposure_time = models.FloatField(blank=True, null=True)
    iso_speed = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return _str(
            self.key,
            title=self.title,
            timestamp=self.timestamp.isoformat()
        )

    @property
    def filename(self):
        return self.key.split('/')[-1]

    @property
    def thumbnail_height(self):
        return 256

    @property
    def thumbnail_width(self):
        return round(self.width / self.height * self.thumbnail_height)

    def to_json(self):
        album_key = self.album.key if self.album else None

        return dict(
            **super().to_json(),
            key=self.key,
            filename=self.filename,
            album=album_key,
            timestamp=self.timestamp.isoformat(),
            height=self.height,
            width=self.width,
            tiny_base64=self.tiny_base64,
            camera_make=self.camera_make,
            camera_model=self.camera_model,
            lens_make=self.lens_make,
            lens_model=self.lens_model,
            focal_length=self.focal_length,
            f_number=self.f_number,
            exposure_time=self.exposure_time,
            iso_speed=self.iso_speed,
        )
