from django.urls import path, include
from . import views

frontend_urls = ([
    path('', views.index, name='index'),
    path('characters/', views.characters, name='characters'),
    path('clusters/', views.clusters, name='clusters'),
    path('speeches/', views.speeches, name='speeches'),
    path('search/', views.search, name='search'),
], 'app')

api_urls = ([
    path('authors/', views.AuthorList.as_view()),
    path('authors/<int:pk>/', views.AuthorDetail.as_view()),
    path('works/', views.WorkList.as_view()),
    path('works/<int:pk>/', views.WorkDetail.as_view()),
    path('speeches/', views.SpeechList.as_view()),
    path('speeches/<int:pk>/', views.SpeechDetail.as_view()),
], 'api')

urlpatterns = [
    path('app/', include(frontend_urls)),
    path('api/', include(api_urls)),
]
