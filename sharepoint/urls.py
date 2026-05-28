from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SharePointConfigViewSet, SharePointSyncLogViewSet, sharepoint_config

router = DefaultRouter()
router.register(r'', SharePointConfigViewSet, basename='sharepoint-api')
router.register(r'sync-logs', SharePointSyncLogViewSet, basename='sharepoint-sync-log-api')

urlpatterns = [
    path('api/', include(router.urls)),
    path('sharepoint/', sharepoint_config, name='sharepoint_config'),
]
