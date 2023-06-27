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
from .models import Author, Work, Character, CharacterInstance, Speech, SpeechCluster, SpeechTag
from .serializers import MetadataSerializer
from .serializers import AuthorSerializer, WorkSerializer, CharacterSerializer, CharacterInstanceSerializer, SpeechSerializer, SpeechClusterSerializer
import csv

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
    work_lang = filters.ChoiceFilter('instances__speeches__work__lang',
                    distinct=True, choices=Work.Language.choices)

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
    id = filters.NumberFilter('char__id')
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
    work_lang = filters.ChoiceFilter('speeches__work__lang', distinct=True,
                            choices=Work.Language.choices)    

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
    spkr_tt = filters.CharFilter('spkr__char__tt')    
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
    addr_tt = filters.CharFilter('addr__char__tt')    
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
    tags = filters.ChoiceFilter('tags__type', choices=SpeechTag.TagType.choices)

    cluster_id = filters.NumberFilter('cluster__id')
    
    work_id = filters.NumberFilter('work__id')
    work_title = filters.CharFilter('work__title')
    work_urn = filters.CharFilter('work__urn')
    work_wd = filters.CharFilter('work__wd')
    work_lang = filters.ChoiceFilter('work__lang', choices=Work.Language.choices)
    
    author_id = filters.NumberFilter('work__author__id')
    author_name = filters.CharFilter('work__author__name')
    author_wd = filters.CharFilter('work__author__wd')
    author_urn = filters.CharFilter('work__author__urn')
        
    class Meta:
        model = Speech
        distinct = True        
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
    spkr_tt = filters.CharFilter('speech__spkr__char__tt', distinct=True)    
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
    addr_tt = filters.CharFilter('speech__addr__char__tt', distinct=True)    
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
    paginate_by = PAGE_SIZE
    
    _valid_params = [
        ('lang', str),
        ('page_size', int),
    ]
    
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # add useful info
        context['params'] = self.params
        context['lang_choices'] = Work.Language.choices
        
        return context

    def get_queryset(self):
        # collect user search params
        self.params = ValidateParams(self.request, self._valid_params)    

        # construct query
        query = []
        
        # language
        if 'lang' in self.params:
            query.append(Q(work__lang=self.params['lang']))
        
        # get query set
        qs = Author.objects.filter(*query).distinct()
        
        # pagination
        if 'page_size' in self.params:
            if self.params['page_size'] > 0:
                self.paginate_by = self.params['page_size']
            else:
                self.paginate_by = qs.count() + 1

        return qs


class AppWorkList(ListView):
    model = Work
    template_name = 'speechdb/work_list.html'
    paginate_by = PAGE_SIZE
    
    _valid_params = [
        ('lang', str),
        ('auth_id', int),
        ('page_size', int),
    ]
    
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # add useful info
        context['params'] = self.params
        context['lang_choices'] = Work.Language.choices
        context['authors'] = Author.objects.all()
        
        return context

    def get_queryset(self):
        # collect user search params
        self.params = ValidateParams(self.request, self._valid_params)    

        # construct query
        query = []
        
        # author by id
        if 'auth_id' in self.params:
            query.append(Q(author=self.params['auth_id']))

        if 'lang' in self.params:
            query.append(Q(lang=self.params['lang']))
        
        # get query set
        qs = Work.objects.filter(*query).distinct()
        # pagination
        if 'page_size' in self.params:
            if self.params['page_size'] > 0:
                self.paginate_by = self.params['page_size']
            else:
                self.paginate_by = qs.count() + 1
          

        return qs


class AppCharacterList(LoginRequiredMixin, ListView):
    model = Character
    template_name = 'speechdb/character_list.html'
    paginate_by = PAGE_SIZE
    _valid_params = [
        ('gender', str),
        ('being', str),
        ('number', str),
        ('lang', str),
        ('auth_id', int),
        ('work_id', int),
        ('manto', str),        
        ('wd', str),
        ('tt', str),        
        ('page_size', int),  
    ]
    
    # authentication
    login_url = '/app/login/'
    
    
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # add useful info
        context['params'] = self.params
        context['lang_choices'] = Work.Language.choices
        context['authors'] = Author.objects.all()                
        context['works'] = Work.objects.all()        
        context['character_being_choices'] = Character.CharacterBeing.choices
        context['character_number_choices'] = Character.CharacterNumber.choices
        context['character_gender_choices'] = Character.CharacterGender.choices        
       
        return context
    
    def get_queryset(self):
        # collect user search params
        self.params = ValidateParams(self.request, self._valid_params)
        
        # construct query
        query = []
        
        if 'gender' in self.params:
            query.append(Q(gender=self.params['gender']))
        
        if 'being' in self.params:
            query.append(Q(being=self.params['being']))
            
        if 'number' in self.params:
            query.append(Q(number=self.params['number']))

        if 'manto' in self.params:
            query.append(Q(manto=self.params['manto']))

        if 'wd' in self.params:
            query.append(Q(wd=self.params['wd']))

        if 'tt' in self.params:
            query.append(Q(tt=self.params['tt']))

        if 'auth_id' in self.params:
            query.append(Q(instances__speeches__work__author=self.params['auth_id'])|
                        Q(instances__addresses__work__author=self.params['auth_id']))

        if 'work_id' in self.params:
            query.append(Q(instances__speeches__work=self.params['work_id'])|
                        Q(instances__addresses__work=self.params['work_id']))
            
        if 'lang' in self.params:
            query.append(Q(instances__speeches__work__lang=self.params['lang'])|
                        Q(instances__addresses__work__lang=self.params['lang']))
        
        qs = Character.objects.filter(*query).distinct().order_by('name')
        
        # calculate some useful counts
        qs = qs.annotate(
            Count('instances__speeches', distinct=True),
            Count('instances__addresses', distinct=True),
        )
        
        # pagination
        if 'page_size' in self.params:
            if self.params['page_size'] > 0:
                self.paginate_by = self.params['page_size']
            else:
                self.paginate_by = qs.count() + 1        
        
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
        ('anon', bool),
        ('char_name', str),
        ('char_gender', str),
        ('char_number', str),
        ('char_being', str),
        ('char_manto', str),
        ('char_wd', str),
        ('char_tt', str),                        
        ('page_size', int),
    ]
    
    # authentication
    login_url = '/app/login/'
    
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # add useful info
        context['params'] = self.params
        context['lang_choices'] = Work.Language.choices
        context['authors'] = Author.objects.all()                
        context['works'] = Work.objects.all()
        context['names'] = CharacterInstance.objects.values_list('name', flat=True).distinct()
        context['characters'] = Character.objects.all()
        context['character_being_choices'] = Character.CharacterBeing.choices
        context['character_number_choices'] = Character.CharacterNumber.choices
        context['character_gender_choices'] = Character.CharacterGender.choices        

        return context
    
    
    def get_queryset(self):
        # collect user search params
        self.params = ValidateParams(self.request, self._valid_params)
        
        # construct query
        query = []
        
        # instance properties        
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
        
        # character properties
        if 'char_name' in self.params:
            query.append(Q(char__name=self.params['char_name']))
            
        if 'char_gender' in self.params:
            query.append(Q(char__gender=self.params['char_gender']))
        
        if 'char_being' in self.params:
            query.append(Q(char__being=self.params['char_being']))

        if 'char_number' in self.params:
            query.append(Q(char__number=self.params['char_number']))

        if 'char_manto' in self.params:
            query.append(Q(char__manto=self.params['char_manto']))

        if 'char_wd' in self.params:
            query.append(Q(char__manto=self.params['char_wd']))

        if 'char_tt' in self.params:
            query.append(Q(char__manto=self.params['char_tt']))
        
        # perform query
        qs = CharacterInstance.objects.filter(*query).order_by('name')
        
        # calculate some useful counts
        qs = qs.annotate(
            Count('speeches', distinct=True),
            Count('addresses', distinct=True),
        )
        
        # pagination
        if 'page_size' in self.params:
            if self.params['page_size'] > 0:
                self.paginate_by = self.params['page_size']
            else:
                self.paginate_by = qs.count() + 1
        
        return qs



class AppSpeechList(LoginRequiredMixin, ListView):
    model = Speech
    template_name = 'speechdb/speech_list.html'
    paginate_by = PAGE_SIZE
    ordering = ['work', 'seq']    
    _valid_params = [
        ('spkr_id', int),
        ('addr_id', int),
        ('char_id', int),
        ('spkr_inst_id', int),
        ('addr_inst_id', int),
        ('char_inst_id', int),
        ('char_inst_name', str),
        ('spkr_inst_name', str),
        ('addr_inst_name', str),
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
        ('spkr_manto', str),
        ('addr_manto', str),               
        ('char_manto', str),
        ('spkr_wd', str),
        ('addr_wd', str),               
        ('char_wd', str),
        ('spkr_tt', str),
        ('addr_tt', str),               
        ('char_tt', str),
        ('cluster_id', int),
        ('spkr_disguised', bool),
        ('type', str),
        ('tags', str),
        ('part', int),
        ('n_parts', int),
        ('level', int),
        ('work_id', int),
        ('auth_id', int),
        ('lang', str),
        ('page_size', int),
    ]
        
    # authentication
    login_url = '/app/login/'
    
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # add useful info
        context['params'] = self.params
        context['reader'] = CTS_READER
        context['lang_choices'] = Work.Language.choices        
        context['authors'] = Author.objects.all()          
        context['works'] = Work.objects.all()
        context['characters'] = Character.objects.all()
        context['character_being_choices'] = Character.CharacterBeing.choices
        context['character_number_choices'] = Character.CharacterNumber.choices
        context['character_gender_choices'] = Character.CharacterGender.choices        
        context['speech_type_choices'] = Speech.SpeechType.choices
        context['anons'] = sorted(set(i.name for i in CharacterInstance.objects.filter(anon=True)))
        context['max_parts'] = Speech.objects.aggregate(Max('part'))['part__max']
        context['tag_choices'] = SpeechTag.TagType.choices
        
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
                Q(addr__char=self.params['char_id'])
            )
        
        # any participant by name
        if 'char_name' in self.params:
            query.append(
                Q(spkr__char__name=self.params['char_name']) |
                Q(addr__char__name=self.params['char_name'])
            )

        # any participant by being
        if 'char_being' in self.params:
            query.append(
                Q(spkr__being=self.params['char_being']) |
                Q(addr__being=self.params['char_being'])
            )
            
        # any participant by gender
        if 'char_gender' in self.params:
            query.append(
                Q(spkr__gender=self.params['char_gender']) |
                Q(addr__gender=self.params['char_gender'])
            )
        
        # speaker by id
        if 'spkr_id' in self.params:
            query.append(Q(spkr__char=self.params['spkr_id']))

        # speaker by instance id
        if 'spkr_inst_id' in self.params:
            query.append(Q(spkr__id=self.params['spkr_inst_id']))
        
        # speaker by instance name
        if 'spkr_inst_name' in self.params:
            query.append(Q(spkr__name=self.params['spkr_inst_name']))
            
        # speaker by name
        if 'spkr_name' in self.params:
            query.append(Q(spkr__char__name=self.params['spkr_name']))

        # speaker by being
        if 'spkr_being' in self.params:
            query.append(Q(spkr__being=self.params['spkr_being']))

        # speaker by gender
        if 'spkr_gender' in self.params:
            query.append(Q(spkr__gender=self.params['spkr_gender']))

        # speaker by number
        if 'spkr_number' in self.params:
            query.append(Q(spkr__number=self.params['spkr_number']))
        
        # speaker disguised
        if 'spkr_disguised' in self.params:
            query.append(Q(spkr__disguise__isnull=not(self.params['spkr_disguised'])))

        # speaker by manto
        if 'spkr_manto' in self.params:
            query.append(Q(spkr__char__manto=self.params['spkr_manto']))

        # speaker by wikidata
        if 'spkr_wd' in self.params:
            query.append(Q(spkr__char__wd=self.params['spkr_wd']))

        # speaker by topostext
        if 'spkr_tt' in self.params:
            query.append(Q(spkr__char__tt=self.params['spkr_tt']))
                    
        # addressee by id
        if 'addr_id' in self.params:
            query.append(Q(addr__char=self.params['addr_id']))

        # addressee by instance id
        if 'addr_inst_id' in self.params:
            query.append(Q(addr__id=self.params['addr_inst_id']))
        
        # addressee by instance name
        if 'addr_inst_name' in self.params:
            query.append(Q(addr__name=self.params['addr_inst_name']))

        # addressee by name
        if 'addr_name' in self.params:
            query.append(Q(addr__char__name=self.params['addr_name']))

        # addressee by being
        if 'addr_being' in self.params:
            query.append(Q(addr__being=self.params['addr_being']))

        # addressee by gender
        if 'addr_gender' in self.params:
            query.append(Q(addr__gender=self.params['addr_gender']))

        # addressee by number
        if 'addr_number' in self.params:
            query.append(Q(addr__number=self.params['addr_number']))

        # speaker by manto
        if 'addr_manto' in self.params:
            query.append(Q(addr__char__manto=self.params['addr_manto']))

        # speaker by wikidata
        if 'addr_wd' in self.params:
            query.append(Q(addr__char__wd=self.params['addr_wd']))

        # speaker by topostext
        if 'addr_tt' in self.params:
            query.append(Q(addr__char__tt=self.params['addr_tt']))
                     

        if 'cluster_id' in self.params:
            query.append(Q(cluster__pk=self.params['cluster_id']))
        
        if 'type' in self.params:
            query.append(Q(type=self.params['type']))
        
        if 'part' in self.params:
            query.append(Q(part=self.params['part']))
        
        if 'n_parts' in self.params:
            query.append(Q(cluster__speech__count=self.params['n_parts']))

        if 'level' in self.params:
            query.append(Q(level=self.params['level']))
        
        if 'work_id' in self.params:
            query.append(Q(work__pk=self.params['work_id']))

        if 'auth_id' in self.params:
            query.append(Q(work__author__pk=self.params['auth_id']))
            
        if 'lang' in self.params:
            query.append(Q(work__lang=self.params['lang']))

        if 'tags' in self.params:
            query.append(Q(tags__type=self.params['tags']))
  
        qs = qs.filter(*query)
        qs = qs.order_by('seq')
        qs = qs.order_by('work')
        
        # pagination
        if 'page_size' in self.params:
            if self.params['page_size'] > 0:
                self.paginate_by = self.params['page_size']
            else:
                self.paginate_by = qs.count() + 1

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
        ('spkr_name', str),
        ('addr_name', str), 
        ('char_name', str), 
        ('spkr_inst_name', str),
        ('addr_inst_name', str),
        ('char_inst_name', str),
        ('spkr_being', str),
        ('addr_being', str),
        ('char_being', str),
        ('spkr_gender', str),
        ('addr_gender', str),               
        ('char_gender', str),
        ('cluster_id', int),
        ('type', str),
        ('n_parts', int),
        ('work_id', int),
        ('auth_id', int),
        ('lang', str),
        ('page_size', int),        
    ]
    
    # authentication
    login_url = '/app/login/'
    
    def get_queryset(self):
        # collect user search params
        self.params = ValidateParams(self.request, self._valid_params)
        
        # initial set of objects plus annotations
        qs = SpeechCluster.objects.annotate(Count('speech'))
                
        # construct query
        query = []
        
        # any participant by id
        if 'char_id' in self.params:
            query.append(Q(speech__spkr__char=self.params['char_id']) |
                         Q(speech__addr__char=self.params['char_id'])
            )
        
        # any participant by instance name
        if 'char_inst_name' in self.params:
            query.append(Q(speech__spkr__name=self.params['char_inst_name']) |
                         Q(speech__addr__name=self.params['char_inst_name'])
            )

        # any participant by name
        if 'char_name' in self.params:
            query.append(Q(speech__spkr__char__name=self.params['char_name']) |
                         Q(speech__addr__char__name=self.params['char_name'])
            )

        # any participant by being
        if 'char_being' in self.params:
            query.append(Q(speech__spkr__being=self.params['char_being']) |
                         Q(speech__addr__being=self.params['char_being'])
            )

        # any participant by gender
        if 'char_gender' in self.params:
            query.append(Q(speech__spkr__gender=self.params['char_gender']) |
                         Q(speech__addr__gender=self.params['char_gender'])
            )
        
        # speaker by id
        if 'spkr_id' in self.params:
            query.append(Q(speech__spkr__char=self.params['spkr_id']))
        
        # speaker by instance name
        if 'spkr_inst_name' in self.params:
            query.append(Q(speech__spkr__name=self.params['spkr_inst_name']))
            
        # speaker by name
        if 'spkr_name' in self.params:
            query.append(Q(speech__spkr__char__name=self.params['spkr_name']))

        # speaker by being
        if 'spkr_being' in self.params:
            query.append(Q(speech__spkr__being=self.params['spkr_being']))

        # speaker by gender
        if 'spkr_gender' in self.params:
            query.append(Q(speech__spkr__gender=self.params['spkr_gender']))
        
        # addressee by id
        if 'addr_id' in self.params:
            query.append(Q(speech__addr__char=self.params['addr_id']))
        
        # addressee by instance name
        if 'addr_inst_name' in self.params:
            query.append(Q(speech__addr__name=self.params['addr_inst_name']))

        # addressee by name
        if 'addr_name' in self.params:
            query.append(Q(speech__addr__char__name=self.params['addr_name']))

        # addressee by being
        if 'addr_being' in self.params:
            query.append(Q(speech__addr__being=self.params['addr_being']))

        # addressee by gender
        if 'addr_gender' in self.params:
            query.append(Q(speech__addr__gender=self.params['addr_gender']))

        if 'cluster_id' in self.params:
            query.append(Q(pk=self.params['cluster_id']))
        
        if 'type' in self.params:
            query.append(Q(speech__type=self.params['type']))
                
        if 'n_parts' in self.params:
            query.append(Q(speech__count=self.params['n_parts']))
        
        if 'work_id' in self.params:
            query.append(Q(speech__work__pk=self.params['work_id']))

        if 'auth_id' in self.params:
            query.append(Q(speech__work__author__pk=self.params['auth_id']))
            
        if 'lang' in self.params:
            query.append(Q(speech__work__lang=self.params['lang']))
        
        # perform query
        qs = qs.filter(*query).distinct()

        # pagination
        if 'page_size' in self.params:
            if self.params['page_size'] > 0:
                self.paginate_by = self.params['page_size']
            else:
                self.paginate_by = qs.count() + 1        
        
        return qs
    
    # authentication
    login_url = '/app/login/'
    
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # add useful info
        context['params'] = self.params
        context['lang_choices'] = Work.Language.choices
        context['authors'] = Author.objects.all()                
        context['works'] = Work.objects.all()
        context['clusters'] = SpeechCluster.objects.all()
        context['characters'] = Character.objects.all()
        context['anons'] = sorted(set(i.name for i in CharacterInstance.objects.filter(anon=True)))        
        context['character_being_choices'] = Character.CharacterBeing.choices
        context['character_number_choices'] = Character.CharacterNumber.choices
        context['character_gender_choices'] = Character.CharacterGender.choices        
        context['speech_type_choices'] = Speech.SpeechType.choices
        
        return context


class AppCharacterInstanceDetail(DetailView):
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
        context['characters'] = Character.objects.all()
        context['names'] = sorted(set([c.name for c in CharacterInstance.objects.all()]))
        context['character_being_choices'] = Character.CharacterBeing.choices
        context['character_number_choices'] = Character.CharacterNumber.choices
        context['character_gender_choices'] = Character.CharacterGender.choices        
                
        return context


class AppCharacterDetail(DetailView):
    model = Character
    template_name = 'speechdb/character_detail.html'
    context_object_name = 'char'
    
    # authentication
    login_url = '/app/login/'
    
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # add useful info
        context['reader'] = CTS_READER
        context['characters'] = Character.objects.all()
        context['character_being_choices'] = Character.CharacterBeing.choices
        context['character_number_choices'] = Character.CharacterNumber.choices
        context['character_gender_choices'] = Character.CharacterGender.choices        
        
        return context


class AppSpeechClusterDetail(DetailView):
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

