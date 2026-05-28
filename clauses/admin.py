from django.contrib import admin
from .models import Clause

@admin.register(Clause)
class ClauseAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'risk', 'status')
    search_fields = ('name', 'category')
    list_filter = ('risk', 'status', 'category')
