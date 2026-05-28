from django.contrib import admin
from .models import Contract, RedlineSuggestion, ContractComparison

@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'vendor', 'expiry', 'risk', 'status', 'uploaded')
    search_fields = ('name', 'vendor')
    list_filter = ('risk', 'status', 'expiry')


@admin.register(RedlineSuggestion)
class RedlineSuggestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'contract', 'issue', 'risk', 'status', 'created_at')
    search_fields = ('issue', 'recommendation', 'contract__name')
    list_filter = ('risk', 'status')


@admin.register(ContractComparison)
class ContractComparisonAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'contract_left', 'contract_right', 'exported_by', 'exported_at')
    search_fields = ('title', 'summary', 'external_document')
