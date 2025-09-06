from django.db import models
from django.db.models.signals import pre_delete, pre_save
from django.contrib.sites.models import Site
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

from photo_objects.utils import first_paragraph_textcontent


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

    alt_text = models.TextField(blank=True)

    def __str__(self):
        return _str(
            self.key,
            title=self.title,
            timestamp=self.timestamp.isoformat()
        )

    @property
    def alt(self):
        if self.alt_text:
            return self.alt_text

        if self.description:
            text = first_paragraph_textcontent(self.description)
            if text:
                return text

        return self.title or self.filename

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
            alt_text=self.alt_text,
        )


class PhotoChangeRequest(models.Model):
    class Meta:
        ordering = ["-created_at"]

    created_at = models.DateTimeField(auto_now_add=True)

    photo = models.ForeignKey(
        "Photo",
        on_delete=models.CASCADE,
        related_name="change_requests")

    alt_text = models.TextField()

    def __str__(self):
        return _str(
            self.photo.key,
            created_at=self.created_at.isoformat()
        )

    def to_json(self):
        return dict(
            id=self.id,
            photo=self.photo.key,
            created_at=_timestamp_str(self.created_at),
            alt_text=self.alt_text,
        )


SETTINGS_CACHE = {}


class SiteSettingsManager(models.Manager):
    def get(self, site: Site):
        cached = SETTINGS_CACHE.get(site.id)
        if cached:
            return cached
        settings, _ = self.get_or_create(site=site)
        SETTINGS_CACHE[site.id] = settings
        return settings


class SiteSettings(models.Model):
    class Meta:
        verbose_name_plural = "site settings"

    site = models.OneToOneField(
        Site, on_delete=models.CASCADE, related_name="settings")

    description = models.TextField(blank=True)
    preview_image = models.ForeignKey(
        Photo, blank=True, null=True, on_delete=models.SET_NULL)

    objects = SiteSettingsManager()

    def __str__(self):
        return f"Settings for {self.site.name}"


def clear_cached_settings(sender, **kwargs):
    site_id = kwargs.get("instance").site.id
    if site_id in SETTINGS_CACHE:
        del SETTINGS_CACHE[site_id]


pre_save.connect(clear_cached_settings, sender=SiteSettings)
pre_delete.connect(clear_cached_settings, sender=SiteSettings)
