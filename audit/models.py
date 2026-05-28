from django.db import models
from django.conf import settings

class AuditLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=128)
    target = models.CharField(max_length=255)
    time = models.DateTimeField(auto_now_add=True)
    ip = models.CharField(max_length=64, default='Internal')

    def __str__(self):
        return f"{self.user} {self.action} {self.target}"
