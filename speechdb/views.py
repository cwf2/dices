from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Max
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
                    print("Value Error")
                    pass
    return params

#
# API filters
#

class AuthorFilter(filters.FilterSet):
    class Meta:
        model = Author
        fields = ['id', 'name', 'wd']


class WorkFilter(filters.FilterSet):
    author_id = filters.NumberFilter('author__id')
    author_name = filters.CharFilter('author__name')
    author_wd = filters.CharFilter('author__wd')
    author_urn = filters.CharFilter('author__urn')    
    
    class Meta:
        model = Work
        fields = ['id', 'title', 'wd', 'urn', 
                    'author_name', 'author_id', 'author_wd']


class CharacterFilter(filters.FilterSet):
    class Meta:
        model = Character
        fields = ['id', 'name', 'wd', 'manto', 'gender', 'number', 'being']


class CharacterInstanceFilter(filters.FilterSet):
    name = filters.CharFilter('name')
    gender = filters.ChoiceFilter('gender', 
                    choices=Character.CharacterGender.choices)
    number = filters.ChoiceFilter('number',
                    choices=Character.CharacterNumber.choices)
    being = filters.ChoiceFilter('being',
                    choices=Character.CharacterBeing.choices)
    anon = filters.BooleanFilter('anon')
    char_id = filters.NumberFilter('char__id')
    char_name = filters.CharFilter('char__name')
    char_wd = filters.CharFilter('char__wd')
    char_manto = filters.CharFilter('char__manto')
    char_gender = filters.ChoiceFilter('char__gender', 
                    choices=Character.CharacterGender.choices)
    char_number = filters.ChoiceFilter('char__number',
                    choices=Character.CharacterNumber.choices)
    char_being = filters.ChoiceFilter('char__being',
                    choices=Character.CharacterBeing.choices)
    
    class Meta:
        model = CharacterInstance
        fields = ['id', 'name', 'gender', 'number', 'being', 'anon', 
                    'char_id', 'char_name', 'char_wd', 'char_manto',
                    'char_gender', 'char_number', 'char_being']


class SpeechFilter(filters.FilterSet):
    spkr_id = filters.NumberFilter('spkr__char__id')
    spkr_name = filters.CharFilter('spkr__name')
    spkr_manto = filters.CharFilter('spkr__char__manto')
    spkr_wd = filters.CharFilter('spkr__char__wd')
    spkr_gender = filters.ChoiceFilter('spkr__gender', 
                    choices=Character.CharacterGender.choices)
    spkr_number = filters.ChoiceFilter('spkr__number',
                    choices=Character.CharacterNumber.choices)
    spkr_being = filters.ChoiceFilter('spkr__being',
                    choices=Character.CharacterBeing.choices)
    spkr_anon = filters.BooleanFilter('spkr__anon')
    
    addr_id = filters.NumberFilter('addr__char__id')
    addr_name = filters.CharFilter('addr__name')
    addr_manto = filters.CharFilter('addr__char__manto')
    addr_wd = filters.CharFilter('addr__char__wd')
    addr_gender = filters.ChoiceFilter('addr__gender', 
                    choices=Character.CharacterGender.choices)
    addr_number = filters.ChoiceFilter('addr__number',
                    choices=Character.CharacterNumber.choices)
    addr_being = filters.ChoiceFilter('addr__being',
                    choices=Character.CharacterBeing.choices)
    addr_anon = filters.BooleanFilter('addr__anon')
    
    spkr_inst = filters.NumberFilter('spkr__id')
    addr_inst = filters.NumberFilter('addr__id')
    
    type = filters.ChoiceFilter('type', choices=Speech.SpeechType.choices)

    cluster_id = filters.NumberFilter('cluster__id')
    
    work_id = filters.NumberFilter('work__id')
    work_title = filters.CharFilter('work__title')
    work_urn = filters.CharFilter('work__urn')
    work_wd = filters.CharFilter('work__wd')
    
    author_id = filters.NumberFilter('work__author__id')
    author_name = filters.CharFilter('work__author__name')
    author_wd = filters.CharFilter('work__author__wd')
    author_urn = filters.CharFilter('work__author__urn')
        
    class Meta:
        model = Speech
        fields = ['id',
            'spkr_id', 'spkr_name', 'spkr_manto', 'spkr_wd', 'spkr_gender',
            'spkr_number', 'spkr_being', 'spkr_anon',
            'addr_id', 'addr_name', 'addr_manto', 'addr_wd', 'addr_gender',
            'addr_number', 'addr_being', 'addr_anon',
            'spkr_inst', 'addr_inst',
            'type', 
            'cluster_id',
            'work_id', 'work_title', 'work_urn', 'work_wd',
            'author_id', 'author_name', 'author_urn', 'author_wd',
            'part']


class SpeechClusterFilter(filters.FilterSet):
    class Meta:
        model = SpeechCluster
        fields = ['id']

#
# API class-based views
#

class AuthorList(ListAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    filterset_class = AuthorFilter


class AuthorDetail(RetrieveAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer


class WorkList(ListAPIView):
    queryset = Work.objects.all()
    serializer_class = WorkSerializer
    filterset_class = WorkFilter


class WorkDetail(RetrieveAPIView):
    queryset = Work.objects.all()
    serializer_class = WorkSerializer


class CharacterList(ListAPIView):
    queryset = Character.objects.all()
    serializer_class = CharacterSerializer
    filterset_class = CharacterFilter


class CharacterDetail(RetrieveAPIView):
    queryset = Character.objects.all()
    serializer_class = CharacterSerializer


class CharacterInstanceList(ListAPIView):
    queryset = CharacterInstance.objects.all()
    serializer_class = CharacterInstanceSerializer
    filterset_class = CharacterInstanceFilter


class CharacterInstanceDetail(RetrieveAPIView):
    queryset = CharacterInstance.objects.all()
    serializer_class = CharacterInstanceSerializer


class SpeechList(ListAPIView):
    queryset = Speech.objects.all()
    serializer_class = SpeechSerializer
    filterset_class = SpeechFilter


class SpeechDetail(RetrieveAPIView):
    queryset = Speech.objects.all()
    serializer_class = SpeechSerializer


class SpeechClusterList(ListAPIView):
    queryset = SpeechCluster.objects.all()
    serializer_class = SpeechClusterSerializer
    filterset_class = SpeechClusterFilter    


class SpeechClusterDetail(RetrieveAPIView):
    queryset = SpeechCluster.objects.all()
    serializer_class = SpeechClusterSerializer
    

#
# Web frontend class-based views
#

class AppAuthorList(ListView):
    model = Author
    template_name = 'speechdb/author_list.html'
    queryset = Author.objects.all()
    paginate_by = PAGE_SIZE


class AppWorkList(ListView):
    model = Work
    template_name = 'speechdb/work_list.html'
    queryset = Work.objects.all()
    paginate_by = PAGE_SIZE


class AppCharacterList(ListView):
    model = Character
    template_name = 'speechdb/character_list.html'
    queryset = Character.objects.all()
    paginate_by = PAGE_SIZE
    _valid_params = [
        ('name', str),
        ('gender', str)
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
        
        if 'gender' in self.params:
            query.append(Q(gender=self.params['gender']))
        
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
        ('gender', str)
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


class AppCharacterInstanceDetail(DetailView):
    model = CharacterInstance
    template_name = 'speechdb/characterinstance_detail.html'
    context_object_name = 'inst'
    
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # add useful info
        context['reader'] = CTS_READER
        
        return context


class AppCharacterDetail(DetailView):
    model = Character
    template_name = 'speechdb/character_detail.html'
    context_object_name = 'char'
    
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # add useful info
        context['reader'] = CTS_READER
        
        return context


class AppSpeechList(ListView):
    model = Speech
    template_name = 'speechdb/speech_list.html'
    paginate_by = PAGE_SIZE
    ordering = ['work', 'seq']    
    _valid_params = [
        ('spkr_id', int),
        ('addr_id', int),
        ('char_id', int),
        ('char_inst', int),
        ('spkr_inst', int),
        ('addr_inst', int),
        ('cluster_id', int),
        ('type', str),
        ('part', int),
        ('n_parts', int),
        ('work_id', int),
    ]
    
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # add useful info
        context['reader'] = CTS_READER
        context['works'] = Work.objects.all()
        context['characters'] = Character.objects.all()
        context['speech_types'] = Speech.SpeechType.choices
        context['search_params'] = self.params.items()
        
        return context
     
    def get_queryset(self):
        # collect user search params
        self.params = ValidateParams(self.request, self._valid_params)
        
        # initial set of objects plus annotations
        qs = Speech.objects.annotate(Count('cluster__speech'))
        
        # construct query
        query = []
        
        # any participant
        if 'char_id' in self.params:
            query.append(
                Q(spkr__char=self.params['char_id']) | 
                Q(spkr__disg=self.params['char_id']) | 
                Q(addr__char=self.params['char_id']) | 
                Q(addr__disg=self.params['char_id'])
            )
        
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
        
        if 'type' in self.params:
            query.append(Q(type=self.params['type']))
        
        if 'part' in self.params:
            query.append(Q(part=self.params['part']))
        
        if 'n_parts' in self.params:
            query.append(Q(cluster__speech__count=self.params['n_parts']))
        
        if 'work_id' in self.params:
            query.append(Q(cluster__work__pk=self.params['work_id']))
        
        qs = qs.filter(*query)
        qs = qs.order_by('seq')
        qs = qs.order_by('work')

        return qs
        

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


class AppSpeechClusterDetail(DetailView):
    model = SpeechCluster
    template_name = 'speechdb/speechcluster_detail.html'
    context_object_name = 'cluster'
    
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # add useful info
        context['reader'] = CTS_READER
        
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
        context['max_parts'] = Speech.objects.aggregate(Max('part'))['part__max']
        context['speech_types'] = Speech.SpeechType.choices
        return context


class AppSpeechClusterSearch(TemplateView):
    template_name = 'speechdb/speechcluster_search.html'
    
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # add useful info
        context['works'] = Work.objects.all()
        context['characters'] = Character.objects.all()
        context['speech_types'] = Speech.SpeechType.choices
        return context


class AppCharacterSearch(TemplateView):
    template_name = 'speechdb/character_search.html'
    
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # add useful info
        context['characters'] = Character.objects.all()
        return context
