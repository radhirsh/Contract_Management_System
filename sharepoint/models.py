from django.db import models

class SharePointConfig(models.Model):
    url = models.URLField()
    folder = models.CharField(max_length=255)
    auto_sync = models.BooleanField(default=True)
    meta_sync = models.BooleanField(default=True)
    last_sync = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.url


class SharePointSyncLog(models.Model):
    STATUS_CHOICES = [
        ('Success', 'Success'),
        ('Failed', 'Failed'),
        ('Warning', 'Warning'),
    ]
    config = models.ForeignKey(SharePointConfig, on_delete=models.CASCADE, related_name='sync_logs')
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default='Success')
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.status} - {self.created_at}"
