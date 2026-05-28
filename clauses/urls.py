from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClauseViewSet, clause_list

router = DefaultRouter()
router.register(r'', ClauseViewSet, basename='clause-api')

urlpatterns = [
    path('api/', include(router.urls)),
    path('clauses/', clause_list, name='clause_list'),
]
