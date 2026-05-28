from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuditLogViewSet, audit_log_list

router = DefaultRouter()
router.register(r'', AuditLogViewSet, basename='auditlog-api')

urlpatterns = [
    path('api/', include(router.urls)),
    path('audit/', audit_log_list, name='audit_log_list'),
]
