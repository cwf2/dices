from django.urls import path
from . import views

app_name = 'speechdb'

urlpatterns = [
#    path('', views.IndexView.as_view(), name='index'),
    path('characters', views.characters, name='characters'),
    path('clusters', views.clusters, name='clusters'),
]
