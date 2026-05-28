from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ContractViewSet,
    RedlineSuggestionViewSet,
    ContractComparisonViewSet,
    dashboard,
    contract_list,
    contract_detail,
    contract_edit,
    contract_delete,
    upload_contract,
    contract_workbench,
    redline_recommendations,
    redline_update_status,
    redline_run_ai,
    contract_view_document,
    contract_download,
    contract_comparisons,
    comparison_create,
    comparison_detail,
    comparison_export,
)

router = DefaultRouter()
router.register(r'', ContractViewSet, basename='contract-api')
router.register(r'redline-suggestions', RedlineSuggestionViewSet, basename='redline-suggestion-api')
router.register(r'comparisons', ContractComparisonViewSet, basename='contract-comparison-api')

urlpatterns = [
    path('api/', include(router.urls)),
    path('', dashboard, name='dashboard'),
    path('contracts/', contract_list, name='contract_list'),
    path('contracts/upload/', upload_contract, name='upload_contract'),
    path('contracts/workbench/', contract_workbench, name='contract_workbench'),
    path('contracts/workbench/<str:pk>/', contract_workbench, name='contract_workbench_contract'),
    path('contracts/<str:pk>/', contract_detail, name='contract_detail'),
    path('contracts/<str:pk>/edit/', contract_edit, name='contract_edit'),
    path('contracts/<str:pk>/delete/', contract_delete, name='contract_delete'),
    path('contracts/<str:pk>/download/', contract_download, name='contract_download'),
    path('contracts/<str:pk>/view/', contract_view_document, name='contract_view_document'),
    path('contracts/<str:pk>/redline-ai/', redline_run_ai, name='redline_run_ai'),
    path('redline/', redline_recommendations, name='redline_recommendations'),
    path('redline/<int:pk>/update/', redline_update_status, name='redline_update_status'),
    path('comparisons/', contract_comparisons, name='contract_comparisons'),
    path('comparisons/create/', comparison_create, name='comparison_create'),
    path('comparisons/<int:pk>/', comparison_detail, name='comparison_detail'),
    path('comparisons/<int:pk>/export/', comparison_export, name='comparison_export'),
]

