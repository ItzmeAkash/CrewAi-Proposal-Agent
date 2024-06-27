# In urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('human_input/', views.human_input, name='human_input'),
    path('agent_status/', views.agent_status_view, name='agent_status'),
    path('download/', views.download_files, name='download_files'), 
]
