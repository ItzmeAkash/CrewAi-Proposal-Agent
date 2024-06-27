from django.urls import path
from . import views
from .views import index, human_input

urlpatterns = [
    path('', index, name='index'),
    path('human_input/', human_input, name='human_input'),
     path('agent_status/', views.agent_status_view, name='agent_status'),
]