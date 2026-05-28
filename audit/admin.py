from django.contrib import admin
from .models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'action', 'target', 'time', 'ip')
    search_fields = ('user__name', 'action', 'target', 'ip')
    list_filter = ('action', 'user')
