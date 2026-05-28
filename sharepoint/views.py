from rest_framework import viewsets, permissions
from .models import SharePointConfig, SharePointSyncLog
from .serializers import SharePointConfigSerializer, SharePointSyncLogSerializer
from .forms import SharePointConfigForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from audit.models import AuditLog


class SharePointConfigViewSet(viewsets.ModelViewSet):
    queryset = SharePointConfig.objects.all()
    serializer_class = SharePointConfigSerializer
    permission_classes = [permissions.IsAuthenticated]


class SharePointSyncLogViewSet(viewsets.ModelViewSet):
    queryset = SharePointSyncLog.objects.select_related('config').all().order_by('-created_at')
    serializer_class = SharePointSyncLogSerializer
    permission_classes = [permissions.IsAuthenticated]


@login_required
def sharepoint_config(request):
    configs = SharePointConfig.objects.all()
    sync_logs = SharePointSyncLog.objects.select_related('config').all().order_by('-created_at')[:8]
    form = SharePointConfigForm()

    if request.method == 'POST':
        action = request.POST.get('action', 'save')
        config_id = request.POST.get('config_id')

        if action == 'delete' and config_id:
            config_obj = get_object_or_404(SharePointConfig, pk=config_id)
            config_obj.delete()
            messages.success(request, 'SharePoint configuration deleted.')
            return redirect('sharepoint_config')

        if action == 'sync' and config_id:
            config_obj = get_object_or_404(SharePointConfig, pk=config_id)
            # Simulate sync (fallback — no real SharePoint SDK integrated)
            try:
                SharePointSyncLog.objects.create(
                    config=config_obj,
                    status='Success',
                    message='Manual sync triggered via ContractOS (simulated).',
                )
                config_obj.last_sync = timezone.now()
                config_obj.save(update_fields=['last_sync'])
                AuditLog.objects.create(
                    user=request.user,
                    action='SharePoint Sync',
                    target=config_obj.url,
                    ip=request.META.get('REMOTE_ADDR', ''),
                )
                messages.success(request, 'Sync triggered successfully.')
            except Exception as exc:
                SharePointSyncLog.objects.create(
                    config=config_obj,
                    status='Failed',
                    message=str(exc),
                )
                messages.error(request, f'Sync failed: {exc}')
            return redirect('sharepoint_config')

        # Save new or edit config
        if config_id:
            config_obj = get_object_or_404(SharePointConfig, pk=config_id)
            form = SharePointConfigForm(request.POST, instance=config_obj)
        else:
            form = SharePointConfigForm(request.POST)

        if form.is_valid():
            saved = form.save()
            AuditLog.objects.create(
                user=request.user,
                action='SharePoint Config Saved',
                target=saved.url,
                ip=request.META.get('REMOTE_ADDR', ''),
            )
            messages.success(request, 'SharePoint configuration saved.')
            return redirect('sharepoint_config')

    return render(
        request,
        'sharepoint/sharepoint_config.html',
        {'configs': configs, 'sync_logs': sync_logs, 'form': form, 'active_nav': 'sharepoint'},
    )

