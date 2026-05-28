from django.urls import path
from .views import sharepoint_config

urlpatterns = [
    path('sharepoint/', sharepoint_config, name='sharepoint_config_web'),
]
