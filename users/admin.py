from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'role', 'status')
    search_fields = ('name', 'email')
    list_filter = ('role', 'status')
