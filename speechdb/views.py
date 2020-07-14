from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.views.generic import ListView, DetailView, TemplateView
from django_filters.views import FilterView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from django_filters import rest_framework as filters
from .models import Author, Work, Character, CharacterInstance, Speech, SpeechCluster
from .serializers import AuthorSerializer, WorkSerializer, CharacterSerializer, CharacterInstanceSerializer, SpeechSerializer, SpeechClusterSerializer

import logging
# Get an instance of a logger
logger = logging.getLogger(__name__)

CTS_READER = 'https://scaife.perseus.org/reader/'
PAGE_SIZE = 25

# parameter validation
def ValidateParams(request, valid_params):
    '''collect valid parameters, check types'''
    params = {}
    
    for param, vtype in valid_params:
        if param in request.GET:
            val = request.GET[param][:256].strip()
            if val != '':
                try:
                    params[param] = vtype(val)
                except ValueError:
                    pass
    return params


#
# API class-based views
#

class AuthorList(ListAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer


class AuthorDetail(RetrieveAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer


class WorkList(ListAPIView):
    queryset = Work.objects.all()
    serializer_class = WorkSerializer


class WorkDetail(RetrieveAPIView):
    queryset = Work.objects.all()
    serializer_class = WorkSerializer


class CharacterList(ListAPIView):
    queryset = Character.objects.all()
    serializer_class = CharacterSerializer


class CharacterDetail(RetrieveAPIView):
    queryset = Character.objects.all()
    serializer_class = CharacterSerializer


class CharacterInstanceList(ListAPIView):
    queryset = Character.objects.all()
    serializer_class = CharacterSerializer


class CharacterInstanceDetail(RetrieveAPIView):
    queryset = CharacterInstance.objects.all()
    serializer_class = CharacterInstanceSerializer


class SpeechFilter(filters.FilterSet):
    class Meta:
        model = Speech
        fields = ['spkr', 'addr']


class SpeechList(ListAPIView):
    queryset = Speech.objects.all()
    serializer_class = SpeechSerializer
    filterset_class=SpeechFilter


class SpeechDetail(RetrieveAPIView):
    queryset = Speech.objects.all()
    serializer_class = SpeechSerializer


class SpeechClusterList(ListAPIView):
    queryset = SpeechCluster.objects.all()
    serializer_class = SpeechClusterSerializer


class SpeechClusterDetail(RetrieveAPIView):
    queryset = SpeechCluster.objects.all()
    serializer_class = SpeechClusterSerializer
    

#
# Web frontend class-based views
#

# class AppAuthorList(ListView):
#     model = Author
#     template_name = 'speechdb/author_list.html'
#     queryset = Author.objects.all()
#     paginate_by = PAGE_SIZE
#
#
# class AppWorkList(ListView):
#     model = Work
#     template_name = 'speechdb/work_list.html'
#     queryset = Work.objects.all()
#     paginate_by = PAGE_SIZE


class AppCharacterList(ListView):
    model = Character
    template_name = 'speechdb/character_list.html'
    queryset = Character.objects.all()
    paginate_by = PAGE_SIZE
    _valid_params = [
        ('name', str),
    ]
    
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # add useful info
        context['search_params'] = self.params.items()
       
        return context
    
    def get_queryset(self):
        # collect user search params
        self.params = ValidateParams(self.request, self._valid_params)
        
        # construct query
        query = []
        
        # speaker by id
        if 'name' in self.params:
            query.append(Q(name=self.params['name']))
        
        qs = Character.objects.filter(*query).order_by('name')
        
        # calculate some useful counts
        qs = qs.annotate(
            Count('instances__speeches', distinct=True),
            Count('instances__addresses', distinct=True),
        )
        
        return qs


class AppCharacterInstanceList(ListView):
    model = CharacterInstance
    template_name = 'speechdb/characterinstance_list.html'
    queryset = CharacterInstance.objects.all()
    paginate_by = PAGE_SIZE
    _valid_params = [
        ('name', str),
    ]
     
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # add useful info
        context['search_params'] = self.params.items()
       
        return context
    
    def get_queryset(self):
        # collect user search params
        self.params = ValidateParams(self.request, self._valid_params)
        
        # construct query
        query = []
        
        # speaker by id
        if 'name' in self.params:
            query.append(Q(char__name=self.params['name']))
        
        qs = CharacterInstance.objects.filter(*query).order_by('char__name')
        
        # calculate some useful counts
        qs = qs.annotate(
            Count('speeches', distinct=True),
            Count('addresses', distinct=True),
        )
        
        return qs


class AppSpeechList(ListView):
    model = Speech
    template_name = 'speechdb/speech_list.html'
    paginate_by = PAGE_SIZE
    _valid_params = [
        ('spkr_id', int),
        ('addr_id', int),
        ('spkr_inst', int),
        ('addr_inst', int),
        ('cluster_id', int),
        ('cluster_type', str),
        ('work_id', int),
    ]
        
    
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # add useful info
        context['reader'] = CTS_READER
        context['works'] = Work.objects.all()
        context['characters'] = Character.objects.all()
        context['speech_types'] = SpeechCluster.speech_type_choices
        context['search_params'] = self.params.items()
        
        return context
     
    def get_queryset(self):
        # collect user search params
        self.params = ValidateParams(self.request, self._valid_params)
        
        # construct query
        query = []
        
        # speaker by id
        if 'spkr_id' in self.params:
            query.append(Q(spkr__char=self.params['spkr_id']) | Q(spkr__disg=self.params['spkr_id']))

        # speaker by instance
        if 'spkr_inst' in self.params:
            query.append(Q(spkr=self.params['spkr_inst']))
    
        # addressee by id
        if 'addr_id' in self.params:
            query.append(Q(addr__char=self.params['addr_id']) | Q(addr__disg=self.params['addr_id']))
        
        # addressee by instance
        if 'addr_inst' in self.params:
            query.append(Q(addr=self.params['addr_inst']))
        
        if 'cluster_id' in self.params:
            query.append(Q(cluster__pk=self.params['cluster_id']))
    
        if 'cluster_type' in self.params:
            query.append(Q(cluster__type=self.params['cluster_type']))
    
        if 'work_id' in self.params:
            query.append(Q(cluster__work__pk=self.params['work_id']))
            
        return Speech.objects.filter(*query)
        

class AppSpeechClusterList(ListView):
    model = SpeechCluster
    template_name = 'speechdb/speechcluster_list.html'
    queryset = SpeechCluster.objects.all()
    paginate_by = PAGE_SIZE
    _valid_params = []
    
    def get_queryset(self):
        # collect user search params
        self.params = ValidateParams(self.request, self._valid_params)
        
        # construct query
        query = []
            
        return SpeechCluster.objects.filter(*query)
    
    
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # add useful info
        context['reader'] = CTS_READER
        context['search_params'] = self.params.items()
        
        return context


class AppIndex(TemplateView):
    template_name = 'speechdb/index.html'
    
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # add useful info
        context['works'] = Work.objects.all()
        context['characters'] = Character.objects.all()
        context['speeches'] = Speech.objects.all()
        return context


class AppSpeechSearch(TemplateView):
    template_name = 'speechdb/speech_search.html'
    
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # add useful info
        context['works'] = Work.objects.all()
        context['characters'] = Character.objects.all()
        context['speech_types'] = SpeechCluster.speech_type_choices
        return context


class AppSpeechClusterSearch(TemplateView):
    template_name = 'speechdb/speechcluster_search.html'
    
    # def get_context_data(self, **kwargs):
    #     # Call the base implementation first to get a context
    #     context = super().get_context_data(**kwargs)
    #     # add useful info
    #     context['works'] = Work.objects.all()
    #     context['characters'] = Character.objects.all()
    #     context['speech_types'] = SpeechCluster.speech_type_choices
    #     return context


class AppCharacterSearch(TemplateView):
    template_name = 'speechdb/character_search.html'
    
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # add useful info
        context['characters'] = Character.objects.all()
        return context
    

    
