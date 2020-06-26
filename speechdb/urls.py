from django.urls import path
from . import views

app_name = 'speechdb'

urlpatterns = [
    path('', views.index, name='index'),
    path('characters', views.characters, name='characters'),
    path('clusters', views.clusters, name='clusters'),
    path('speeches', views.speeches, name='speeches'),
    path('search', views.search, name='search'),
]
