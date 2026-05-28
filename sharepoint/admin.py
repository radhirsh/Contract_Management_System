from django.contrib import admin
from .models import SharePointConfig, SharePointSyncLog

@admin.register(SharePointConfig)
class SharePointConfigAdmin(admin.ModelAdmin):
    list_display = ('id', 'url', 'folder', 'auto_sync', 'meta_sync', 'last_sync')
    search_fields = ('url', 'folder')
    list_filter = ('auto_sync', 'meta_sync')


@admin.register(SharePointSyncLog)
class SharePointSyncLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'config', 'status', 'message', 'created_at')
    search_fields = ('message',)
    list_filter = ('status',)
