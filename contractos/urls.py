from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/contracts/', include('contracts.urls')),
    path('api/users/', include('users.urls')),
    path('api/clauses/', include('clauses.urls')),
    path('api/audit/', include('audit.urls')),
    path('api/sharepoint/', include('sharepoint.urls')),
    path('accounts/', include('django.contrib.auth.urls')),  # Enables /accounts/login/ and logout
    path('', include('users.web_urls')),
    path('', include('clauses.web_urls')),
    path('', include('audit.web_urls')),
    path('', include('sharepoint.web_urls')),
    path('', include('contracts.urls')),  # Main UI routes
    path('notifications/', include('notifications.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
