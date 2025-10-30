from django.contrib import admin

from .models import Album, Backup, Photo, PhotoChangeRequest, SiteSettings


class BackupAdmin(admin.ModelAdmin):
    readonly_fields = ["status"]


admin.site.register(Album)
admin.site.register(Photo)
admin.site.register(SiteSettings)
admin.site.register(PhotoChangeRequest)
admin.site.register(Backup, BackupAdmin)
