from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

frontend_urls = ([
    path('', views.AppIndex.as_view(), name='index'),
    path('login/', auth_views.LoginView.as_view(template_name='speechdb/login.html'), name='login'),
    path('logout/', auth_views.logout_then_login, {'login_url':'app:index'}, name='logout'),
    path('characters/', views.AppCharacterList.as_view(), name='characters'),
    path('characters/search', views.AppCharacterSearch.as_view(), name='character_search'),
    path('instances/', views.AppCharacterInstanceList.as_view(), name='instances'),
    path('clusters/', views.AppSpeechClusterList.as_view(), name='clusters'),
    path('clusters/search', views.AppSpeechClusterSearch.as_view(), name='cluster_search'),
    path('speeches/', views.AppSpeechList.as_view(), name='speeches'),
    path('speeches/search', views.AppSpeechSearch.as_view(), name='speech_search'),
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
