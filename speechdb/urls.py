from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('speech/<int:speech_id>', views.speech, name='speech'),
    path('characters', views.characters, name='characters'),
    path('character/<int:character_id>', views.character, name='character'),
]
