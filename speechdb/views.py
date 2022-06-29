from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q, Count, Max
from django.views.generic import ListView, DetailView, TemplateView
from django_filters.views import FilterView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from django_filters import rest_framework as filters
from .models import Metadata
from .models import Author, Work, Character, CharacterInstance, Speech, SpeechCluster
from .serializers import MetadataSerializer
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

class MetadataFilter(filters.FilterSet):
    class Meta:
        model = Metadata
        distinct = True        
        fields = ['name']


class AuthorFilter(filters.FilterSet):
    
    lang = filters.CharFilter('work__lang')
    
    work_id = filters.NumberFilter('work__id')
    work_title = filters.CharFilter('work__title')
    work_urn = filters.CharFilter('work__urn')
    work_wd = filters.CharFilter('work__wd')    
    
    class Meta:
        model = Author
        distinct = True        
        exclude = []


class WorkFilter(filters.FilterSet):
    author_id = filters.NumberFilter('author__id')
    author_name = filters.CharFilter('author__name')
    author_wd = filters.CharFilter('author__wd')
    author_urn = filters.CharFilter('author__urn')    
    
    class Meta:
        model = Work
        exclude = []


class CharacterFilter(filters.FilterSet):
    
    work_id = filters.CharFilter('instances__speeches__work__id',
                    distinct=True)
    work_title = filters.CharFilter('instances__speeches__work__title',
                    distinct=True)
    work_urn = filters.CharFilter('instances__speeches__work__urn',
                    distinct=True)
    work_wd = filters.CharFilter('instances__speeches__work__wd',
                    distinct=True)

    author_id = filters.CharFilter('instances__speeches__work__author__id',
                    distinct=True)
    author_name = filters.CharFilter('instances__speeches__work__author__name',
                    distinct=True)
    author_wd = filters.CharFilter('instances__speeches__work__author__wd',
                    distinct=True)
    author_urn = filters.CharFilter('instances__speeches__work__author__urn',
                    distinct=True)

    inst_name = filters.CharFilter('instances__name', distinct=True)
    inst_gender = filters.ChoiceFilter('instances__gender', distinct=True,
                            choices=Character.CharacterGender.choices)
    inst_number = filters.ChoiceFilter('instances__number', distinct=True,
                            choices=Character.CharacterNumber.choices)
    inst_being = filters.ChoiceFilter('instances__being', distinct=True,
                            choices=Character.CharacterBeing.choices)

    speech_type = filters.CharFilter('instances__speeches__type', distinct=True)
    speech_part = filters.CharFilter('instances__speeches__part', distinct=True)

    
    class Meta:
        model = Character
        exclude = []


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
    wd = filters.CharFilter('char__wd')
    manto = filters.CharFilter('char__manto')
    char_gender = filters.ChoiceFilter('char__gender', 
                    choices=Character.CharacterGender.choices)
    char_number = filters.ChoiceFilter('char__number',
                    choices=Character.CharacterNumber.choices)
    char_being = filters.ChoiceFilter('char__being',
                    choices=Character.CharacterBeing.choices)

    work_id = filters.CharFilter('speeches__work__id', distinct=True)
    work_title = filters.CharFilter('speeches__work__title', distinct=True)
    work_urn = filters.CharFilter('speeches__work__urn', distinct=True)
    work_wd = filters.CharFilter('speeches__work__wd', distinct=True)

    author_id = filters.CharFilter('speeches__work__author__id', distinct=True)
    author_name = filters.CharFilter('speeches__work__author__name',
                    distinct=True)
    author_wd = filters.CharFilter('speeches__work__author__wd', distinct=True)
    author_urn = filters.CharFilter('speeches__work__author__urn',
                    distinct=True)

    speech_type = filters.CharFilter('speeches__type', distinct=True)
    speech_part = filters.CharFilter('speeches__part', distinct=True)
    
    class Meta:
        model = CharacterInstance
        exclude = ['tags']


class SpeechFilter(filters.FilterSet):
    spkr_id = filters.NumberFilter('spkr__char__id')
    spkr_name = filters.CharFilter('spkr__char__name')
    spkr_manto = filters.CharFilter('spkr__char__manto')
    spkr_wd = filters.CharFilter('spkr__char__wd')
    spkr_gender = filters.ChoiceFilter('spkr__char__gender', distinct=True,
                    choices=Character.CharacterGender.choices)
    spkr_number = filters.ChoiceFilter('spkr__char__number', distinct=True,
                    choices=Character.CharacterNumber.choices)
    spkr_being = filters.ChoiceFilter('spkr__char__being', distinct=True,
                    choices=Character.CharacterBeing.choices)

    spkr_inst_id = filters.NumberFilter('spkr__id')
    spkr_inst_name = filters.CharFilter('spkr__name', distinct=True)
    spkr_inst_gender = filters.ChoiceFilter('spkr__gender', distinct=True,
                    choices=Character.CharacterGender.choices)
    spkr_inst_number = filters.ChoiceFilter('spkr__number', distinct=True,
                    choices=Character.CharacterNumber.choices)
    spkr_inst_being = filters.ChoiceFilter('spkr__being', distinct=True,
                    choices=Character.CharacterBeing.choices)
    spkr_anon = filters.BooleanFilter('spkr__anon', distinct=True)
    
    addr_id = filters.NumberFilter('addr__char__id')
    addr_name = filters.CharFilter('addr__char__name')
    addr_manto = filters.CharFilter('addr__char__manto')
    addr_wd = filters.CharFilter('addr__char__wd')
    addr_gender = filters.ChoiceFilter('addr__char__gender', distinct=True,
                    choices=Character.CharacterGender.choices)
    addr_number = filters.ChoiceFilter('addr__char__number', distinct=True,
                    choices=Character.CharacterNumber.choices)
    addr_being = filters.ChoiceFilter('addr__char__being', distinct=True,
                    choices=Character.CharacterBeing.choices)
                    
    addr_inst_id = filters.NumberFilter('addr__id')
    addr_inst_name = filters.CharFilter('addr__name', distinct=True)
    addr_inst_gender = filters.ChoiceFilter('addr__gender', distinct=True,
                    choices=Character.CharacterGender.choices)
    addr_inst_number = filters.ChoiceFilter('addr__number', distinct=True,
                    choices=Character.CharacterNumber.choices)
    addr_inst_being = filters.ChoiceFilter('addr__being', distinct=True,
                    choices=Character.CharacterBeing.choices)
    addr_anon = filters.BooleanFilter('addr__anon', distinct=True)
    
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
        exclude = []


class SpeechClusterFilter(filters.FilterSet):
    
    work_id = filters.NumberFilter('speech__work__id', distinct=True)
    work_title = filters.CharFilter('speech__work__title', distinct=True)
    work_urn = filters.CharFilter('speech__work__urn', distinct=True)
    work_wd = filters.CharFilter('speech__work__wd', distinct=True)

    author_id = filters.NumberFilter('speech__work__author__id', distinct=True)
    author_name = filters.CharFilter('speech__work__author__name', distinct=True)
    author_wd = filters.CharFilter('speech__work__author__wd', distinct=True)
    author_urn = filters.CharFilter('speech__work__author__urn', distinct=True)

    spkr_id = filters.NumberFilter('speech__spkr__char__id', distinct=True)
    spkr_name = filters.CharFilter('speech__spkr__char__name', distinct=True)
    spkr_manto = filters.CharFilter('speech__spkr__char__manto', distinct=True)
    spkr_wd = filters.CharFilter('speech__spkr__char__wd', distinct=True)
    spkr_gender = filters.ChoiceFilter('speech__spkr__char__gender', 
                    choices=Character.CharacterGender.choices, distinct=True)
    spkr_number = filters.ChoiceFilter('speech__spkr__char__number',
                    choices=Character.CharacterNumber.choices, distinct=True)
    spkr_being = filters.ChoiceFilter('speech__spkr__char__being',
                    choices=Character.CharacterBeing.choices, distinct=True)
    
    spkr_inst_id = filters.NumberFilter('speech__spkr__id', distinct=True)
    spkr_inst_name = filters.CharFilter('speech__spkr__name', distinct=True)
    spkr_inst_gender = filters.ChoiceFilter('speech__spkr__gender', 
                    choices=Character.CharacterGender.choices, distinct=True)
    spkr_inst_number = filters.ChoiceFilter('speech__spkr__number',
                    choices=Character.CharacterNumber.choices, distinct=True)
    spkr_inst_being = filters.ChoiceFilter('speech__spkr__being',
                    choices=Character.CharacterBeing.choices, distinct=True)
    spkr_anon = filters.BooleanFilter('speech__spkr__anon', distinct=True)

    addr_id = filters.NumberFilter('speech__addr__char__id', distinct=True)
    addr_name = filters.CharFilter('speech__addr__char__name', distinct=True)
    addr_manto = filters.CharFilter('speech__addr__char__manto', distinct=True)
    addr_wd = filters.CharFilter('speech__addr__char__wd', distinct=True)
    addr_gender = filters.ChoiceFilter('speech__addr__char__gender', 
                    choices=Character.CharacterGender.choices, distinct=True)
    addr_number = filters.ChoiceFilter('speech__addr__char__number',
                    choices=Character.CharacterNumber.choices, distinct=True)
    addr_being = filters.ChoiceFilter('speech__addr__char__being',
                    choices=Character.CharacterBeing.choices, distinct=True)
                    
    addr_inst_id = filters.NumberFilter('speech__addr__id', distinct=True)
    addr_inst_name = filters.CharFilter('speech__addr__name', distinct=True)
    addr_inst_name = filters.CharFilter('speech__addr__name', distinct=True)
    addr_inst_gender = filters.ChoiceFilter('speech__addr__gender', 
                    choices=Character.CharacterGender.choices, distinct=True)
    addr_inst_number = filters.ChoiceFilter('speech__addr__number',
                    choices=Character.CharacterNumber.choices, distinct=True)
    addr_inst_being = filters.ChoiceFilter('speech__addr__being',
                    choices=Character.CharacterBeing.choices, distinct=True)
    addr_anon = filters.BooleanFilter('speech__addr__anon', distinct=True)
    
    class Meta:
        model = SpeechCluster
        exclude = []

#
# API class-based views
#

class MetadataList(ListAPIView):
    queryset = Metadata.objects.all()
    serializer_class = MetadataSerializer
    filterset_class = MetadataFilter

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

class AppMetadataList(ListView):
    model = Metadata
    template_name = 'speechdb/metadata_list.html'
    queryset = Metadata.objects.all()


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


class AppCharacterList(LoginRequiredMixin, ListView):
    model = Character
    template_name = 'speechdb/character_list.html'
    queryset = Character.objects.all()
    paginate_by = PAGE_SIZE
    _valid_params = [
        ('name', str),
        ('gender', str),
        ('being', str),
        ('number', str)
    ]
    
    # authentication
    login_url = '/app/login/'
    
    
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
        
        if 'being' in self.params:
            query.append(Q(being=self.params['being']))

        if 'number' in self.params:
            query.append(Q(number=self.params['number']))
        
        qs = Character.objects.filter(*query).order_by('name')
        
        # calculate some useful counts
        qs = qs.annotate(
            Count('instances__speeches', distinct=True),
            Count('instances__addresses', distinct=True),
        )
        
        return qs


class AppCharacterInstanceList(LoginRequiredMixin, ListView):
    model = CharacterInstance
    template_name = 'speechdb/characterinstance_list.html'
    queryset = CharacterInstance.objects.all()
    paginate_by = PAGE_SIZE
    _valid_params = [
        ('name', str),
        ('gender', str),
        ('number', str),
        ('being', str),
        ('anon', bool)
    ]
    
    # authentication
    login_url = '/app/login/'
    
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
        
        if 'being' in self.params:
            query.append(Q(being=self.params['being']))

        if 'number' in self.params:
            query.append(Q(number=self.params['number']))
         
        if 'anon' in self.params:
            query.append(Q(anon=self.params['anon']))
        
        qs = CharacterInstance.objects.filter(*query).order_by('name')
        
        # calculate some useful counts
        qs = qs.annotate(
            Count('speeches', distinct=True),
            Count('addresses', distinct=True),
        )
        
        return qs


class AppCharacterInstanceDetail(LoginRequiredMixin, DetailView):
    model = CharacterInstance
    template_name = 'speechdb/characterinstance_detail.html'
    context_object_name = 'inst'
    
    # authentication
    login_url = '/app/login/'
    
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # add useful info
        context['reader'] = CTS_READER
        
        return context



class AppCharacterDetail(LoginRequiredMixin, DetailView):
    model = Character
    template_name = 'speechdb/character_detail.html'
    context_object_name = 'char'
    
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # add useful info
        context['reader'] = CTS_READER
        
        return context



class AppSpeechList(LoginRequiredMixin, ListView):
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
        ('spkr_name', str),
        ('addr_name', str),
        ('char_name', str), 
        ('spkr_being', str),
        ('addr_being', str),               
        ('char_being', str),
        ('spkr_number', str),
        ('addr_number', str),               
        ('char_number', str),
        ('spkr_gender', str),
        ('addr_gender', str),               
        ('char_gender', str),
        ('cluster_id', int),
        ('type', str),
        ('part', int),
        ('n_parts', int),
        ('work_id', int),
    ]
        
    # authentication
    login_url = '/app/login/'
    
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # add useful info
        context['reader'] = CTS_READER
        context['works'] = Work.objects.all()
        context['characters'] = Character.objects.all()
        context['character_being_choices'] = Character.CharacterBeing.choices
        context['character_number_choices'] = Character.CharacterNumber.choices
        context['character_gender_choices'] = Character.CharacterGender.choices        
        context['speech_type_choices'] = Speech.SpeechType.choices
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
        
        # any participant by name
        if 'char_name' in self.params:
            query.append(
                Q(spkr__name=self.params['char_name']) |
                Q(addr__name=self.params['char_name'])
            )

        # any participant by being
        if 'char_being' in self.params:
            query.append(
                Q(spkr__being=self.params['char_being']) |
                Q(addr__being=self.params['char_being'])
            )
        
        # speaker by id
        if 'spkr_id' in self.params:
            query.append(Q(spkr__char=self.params['spkr_id']) | Q(spkr__disg=self.params['spkr_id']))
        
        # speaker by instance
        if 'spkr_inst' in self.params:
            query.append(Q(spkr=self.params['spkr_inst']))
            
        # speaker by name
        if 'spkr_name' in self.params:
            query.append(Q(spkr__name=self.params['spkr_name']))

        # speaker by being
        if 'spkr_being' in self.params:
            query.append(Q(spkr__being=self.params['spkr_being']))

        # speaker by gender
        if 'spkr_gender' in self.params:
            query.append(Q(spkr__gender=self.params['spkr_gender']))

        # speaker by number
        if 'spkr_number' in self.params:
            query.append(Q(spkr__number=self.params['spkr_number']))
        
        # addressee by id
        if 'addr_id' in self.params:
            query.append(Q(addr__char=self.params['addr_id']) | Q(addr__disg=self.params['addr_id']))
        
        # addressee by instance
        if 'addr_inst' in self.params:
            query.append(Q(addr=self.params['addr_inst']))

        # addressee by name
        if 'addr_name' in self.params:
            query.append(Q(addr__name=self.params['addr_name']))

        # addressee by being
        if 'addr_being' in self.params:
            query.append(Q(addr__being=self.params['addr_being']))

        # addressee by gender
        if 'addr_gender' in self.params:
            query.append(Q(addr__gender=self.params['addr_gender']))

        # addressee by number
        if 'addr_number' in self.params:
            query.append(Q(addr__number=self.params['addr_number']))            

        if 'cluster_id' in self.params:
            query.append(Q(cluster__pk=self.params['cluster_id']))
        
        if 'type' in self.params:
            query.append(Q(type=self.params['type']))
        
        if 'part' in self.params:
            query.append(Q(part=self.params['part']))
        
        if 'n_parts' in self.params:
            query.append(Q(cluster__speech__count=self.params['n_parts']))
        
        if 'work_id' in self.params:
            query.append(Q(work__pk=self.params['work_id']))
        
        qs = qs.filter(*query)
        qs = qs.order_by('seq')
        qs = qs.order_by('work')

        return qs
        

class AppSpeechClusterList(LoginRequiredMixin, ListView):
    model = SpeechCluster
    template_name = 'speechdb/speechcluster_list.html'
    queryset = SpeechCluster.objects.all()
    paginate_by = PAGE_SIZE
    _valid_params = [
        ('spkr_id', int),
        ('addr_id', int),
        ('char_id', int),
        ('char_inst', int),
        ('spkr_inst', int),
        ('addr_inst', int),
        ('spkr_name', str),
        ('addr_name', str),
        ('char_name', str), 
        ('spkr_being', str),
        ('addr_being', str),               
        ('char_being', str),
        ('cluster_id', int),
        ('type', str),
        ('n_parts', int),
        ('work_id', int),        
    ]
    
    # authentication
    login_url = '/app/login/'
    
    def get_queryset(self):
        # collect user search params
        self.params = ValidateParams(self.request, self._valid_params)
        
        # construct query
        query = []
        
        # any participant
        if 'char_id' in self.params:
            query.append(
                Q(speech__spkr__char=self.params['char_id']) | 
                Q(speech__addr__char=self.params['char_id'])
            )
        
        # any participant by name
        if 'char_name' in self.params:
            query.append(
                Q(speech__spkr__name=self.params['char_name']) |
                Q(speech__addr__name=self.params['char_name'])
            )

        # any participant by being
        if 'char_being' in self.params:
            query.append(
                Q(speech__spkr__being=self.params['char_being']) |
                Q(speech__addr__being=self.params['char_being'])
            )
        
        # speaker by id
        if 'spkr_id' in self.params:
            query.append(Q(speech__spkr__char=self.params['spkr_id']))
        
        # speaker by instance
        if 'spkr_inst' in self.params:
            query.append(Q(speech__spkr=self.params['spkr_inst']))
            
        # speaker by name
        if 'spkr_name' in self.params:
            query.append(Q(speech__spkr__name=self.params['spkr_name']))

        # speaker by name
        if 'spkr_being' in self.params:
            query.append(Q(speech__spkr__being=self.params['spkr_being']))
        
        # addressee by id
        if 'addr_id' in self.params:
            query.append(Q(speech__addr__char=self.params['addr_id']))
        
        # addressee by instance
        if 'addr_inst' in self.params:
            query.append(Q(speech__addr=self.params['addr_inst']))

        # addressee by name
        if 'addr_name' in self.params:
            query.append(Q(speech__addr__name=self.params['addr_name']))

        # addressee by being
        if 'addr_being' in self.params:
            query.append(Q(speech__addr__being=self.params['addr_being']))

        if 'cluster_id' in self.params:
            query.append(Q(pk=self.params['cluster_id']))
        
        if 'type' in self.params:
            query.append(Q(speech__type=self.params['type']))
                
        if 'n_parts' in self.params:
            query.append(Q(speech__count=self.params['n_parts']))
        
        if 'work_id' in self.params:
            query.append(Q(speech__work__pk=self.params['work_id']))
        
        
        return SpeechCluster.objects.filter(*query)
    
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # add useful info
        context['reader'] = CTS_READER
        context['search_params'] = self.params.items()
        
        return context


class AppSpeechClusterDetail(LoginRequiredMixin, DetailView):
    model = SpeechCluster
    template_name = 'speechdb/speechcluster_detail.html'
    context_object_name = 'cluster'
    
    # authentication
    login_url = '/app/login/'
    
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # add useful info
        context['reader'] = CTS_READER
        
        return context


class AppIndex(LoginRequiredMixin, TemplateView):
    template_name = 'speechdb/index.html'

    # authentication
    login_url = '/app/login/'
    
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # add useful info
        context['works'] = Work.objects.all()
        context['characters'] = Character.objects.all()
        context['speeches'] = Speech.objects.all()
        return context


class AppSpeechSearch(LoginRequiredMixin, TemplateView):
    template_name = 'speechdb/speech_search.html'
    
    # authentication
    login_url = '/app/login/'    
    
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # add useful info
        context['works'] = Work.objects.all()
        context['characters'] = Character.objects.all()
        context['max_parts'] = Speech.objects.aggregate(Max('part'))['part__max']
        context['character_being_choices'] = Character.CharacterBeing.choices
        context['character_number_choices'] = Character.CharacterNumber.choices
        context['character_gender_choices'] = Character.CharacterGender.choices        
        context['speech_type_choices'] = Speech.SpeechType.choices

        return context


class AppSpeechClusterSearch(LoginRequiredMixin, TemplateView):
    template_name = 'speechdb/speechcluster_search.html'
    
    # authentication
    login_url = '/app/login/'
    
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # add useful info
        context['clusters'] = SpeechCluster.objects.all()
        context['works'] = Work.objects.all()
        context['characters'] = Character.objects.all()
        context['character_being_choices'] = Character.CharacterBeing.choices
        context['character_number_choices'] = Character.CharacterNumber.choices
        context['character_gender_choices'] = Character.CharacterGender.choices        
        context['speech_type_choices'] = Speech.SpeechType.choices

        return context


class AppCharacterSearch(LoginRequiredMixin, TemplateView):
    template_name = 'speechdb/character_search.html'
    
    # authentication
    login_url = '/app/login/'
    
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # add useful info
        context['characters'] = Character.objects.all()
        context['character_being_choices'] = Character.CharacterBeing.choices
        context['character_number_choices'] = Character.CharacterNumber.choices
        context['character_gender_choices'] = Character.CharacterGender.choices        
        return context

class AppCharacterInstanceSearch(TemplateView):
    template_name = 'speechdb/instances_search.html'
    
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # add useful info
        context['characters'] = Character.objects.all()
        context['names'] = sorted(set([c.name for c in CharacterInstance.objects.all()]))
        context['character_being_choices'] = Character.CharacterBeing.choices
        context['character_number_choices'] = Character.CharacterNumber.choices
        context['character_gender_choices'] = Character.CharacterGender.choices        
        return context
