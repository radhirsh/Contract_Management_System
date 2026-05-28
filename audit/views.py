from rest_framework import viewsets, permissions
from .models import AuditLog
from .serializers import AuditLogSerializer
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

class AuditLogViewSet(viewsets.ModelViewSet):
    queryset = AuditLog.objects.all().order_by('-time')
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]

@login_required
def audit_log_list(request):
    logs = AuditLog.objects.all().order_by('-time')
    return render(request, 'audit/audit_log_list.html', {'logs': logs, 'active_nav': 'audit'})
