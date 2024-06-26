from django.urls import path
from .views import index, human_input

urlpatterns = [
    path('', index, name='index'),
    path('human_input/', human_input, name='human_input'),
]
