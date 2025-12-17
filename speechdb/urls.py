from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from . import views

frontend_urls = ([
    path('', views.AppIndex.as_view(), name='index'),
    path('login/', auth_views.LoginView.as_view(template_name='speechdb/login.html'), name='login'),
    path('logout/', auth_views.logout_then_login, {'login_url':'app:index'}, name='logout'),
    path('meta/', views.AppMetadataList.as_view(), name='meta'),
    path('authors/', views.AppAuthorList.as_view(), name='authors'),
    path('authors/csv/', views.AppAuthorCSV.as_view(), name='authors_csv'),
    path('author/<str:public_id>', views.AppAuthorDetail.as_view(), name="author_detail"),
    path('works/', views.AppWorkList.as_view(), name='works'),
    path('works/csv/', views.AppWorkCSV.as_view(), name="works_csv"),
    path('work/<str:public_id>', views.AppWorkDetail.as_view(), name="work_detail"),
    path('characters/', views.AppCharacterList.as_view(), name='characters'),
    path("characters/csv/", views.AppCharacterCSV.as_view(), name="characters_csv"),
    path('character/<str:public_id>/', views.AppCharacterDetail.as_view(), name='character_detail'),
    path('instances/', views.AppCharacterInstanceList.as_view(), name='instances'),
    path("instances/csv/", views.AppCharacterInstanceCSV.as_view(), name="instances_csv"),
    path('characterinstance/<str:public_id>', views.AppCharacterInstanceDetail.as_view(), name='instance_detail'),
    path('clusters/', views.AppSpeechClusterList.as_view(), name='clusters'),
    path("clusters/csv/", views.AppSpeechClusterCSV.as_view(), name="clusters_csv"),
    path('speechcluster/<str:public_id>/', views.AppSpeechClusterDetail.as_view(), name='cluster_detail'),
    path('speeches/', views.AppSpeechList.as_view(), name='speeches'),
    path('speeches/csv/', views.AppSpeechCSV.as_view(), name='speeches_csv'),
    path('speech/<str:public_id>/', views.AppSpeechDetail.as_view(), name="speech_detail"),
], 'app')

api_urls = ([
    path('meta/', views.MetadataList.as_view()),
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
    path('', RedirectView.as_view(pattern_name='app:index')),
    path('app/', include(frontend_urls)),
    path('api/', include(api_urls)),
]
