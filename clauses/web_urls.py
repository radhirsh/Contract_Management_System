from django.urls import path
from .views import clause_list, clause_add, clause_edit, clause_detail, clause_action, clause_upload

urlpatterns = [
    path('clauses/', clause_list, name='clause_list_web'),
    path('clauses/add/', clause_add, name='clause_add'),
    path('clauses/upload/', clause_upload, name='clause_upload'),
    path('clauses/<str:pk>/', clause_detail, name='clause_detail'),
    path('clauses/<str:pk>/edit/', clause_edit, name='clause_edit'),
    path('clauses/<str:pk>/action/', clause_action, name='clause_action'),
]
