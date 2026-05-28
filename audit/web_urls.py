from django.urls import path
from .views import audit_log_list

urlpatterns = [
    path('audit/', audit_log_list, name='audit_log_list_web'),
]
