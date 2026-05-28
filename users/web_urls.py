from django.urls import path
from .views import register_page, user_list, user_edit, user_toggle_status

urlpatterns = [
    path('register/', register_page, name='register'),
    path('users/', user_list, name='user_list_web'),
    path('users/<int:pk>/edit/', user_edit, name='user_edit'),
    path('users/<int:pk>/toggle-status/', user_toggle_status, name='user_toggle_status'),
]
