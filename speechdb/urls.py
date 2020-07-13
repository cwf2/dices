from django.urls import path, include
from . import views

frontend_urls = ([
    path('', views.AppIndex.as_view(), name='index'),
    path('authors/', views.AppAuthorList.as_view(), name='authors'),
    path('works/', views.AppWorkList.as_view(), name='works'),
    path('characters/', views.AppCharacterList.as_view(), name='characters'),
    path('instances/', views.AppCharacterInstanceList.as_view(), name='instances'),
    path('clusters/', views.AppSpeechClusterList.as_view(), name='clusters'),
    path('speeches/', views.AppSpeechList.as_view(), name='speeches'),
], 'app')

api_urls = ([
    path('authors/', views.AuthorList.as_view()),
    path('authors/<int:pk>/', views.AuthorDetail.as_view()),
    path('works/', views.WorkList.as_view()),
    path('works/<int:pk>/', views.WorkDetail.as_view()),
    path('characters/', views.CharacterList.as_view()),
    path('characters/<int:pk>/', views.CharacterDetail.as_view()),
    path('instances/', views.CharacterInstanceList.as_view()),
    path('instances/<int:pk>/', views.CharacterInstanceDetail.as_view()),
    path('speeches/', views.SpeechList.as_view()),
    path('speeches/<int:pk>/', views.SpeechDetail.as_view()),
    path('clusters/', views.SpeechClusterList.as_view()),
    path('clusters/<int:pk>/', views.SpeechClusterDetail.as_view()),
], 'api')

urlpatterns = [
    path('app/', include(frontend_urls)),
    path('api/', include(api_urls)),
]
