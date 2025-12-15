from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Max
from django.views.generic import ListView, DetailView, TemplateView, View
from django_filters.views import FilterView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from django_filters import rest_framework as filters
from .models import Metadata
from .models import Author, Work, Character, CharacterInstance, Speech, SpeechCluster, SpeechTag
from .serializers import MetadataSerializer
from .serializers import AuthorSerializer, WorkSerializer, CharacterSerializer, CharacterInstanceSerializer, SpeechSerializer, SpeechClusterSerializer
from .forms import InstanceForm, CharacterForm, TextForm, SpeechForm, PagerForm
import csv
import re

import logging
# Get an instance of a logger
logger = logging.getLogger(__name__)

CTS_READER = 'https://scaife.perseus.org/reader/'
PAGE_SIZE = 25


# parameter validation
def ValidateParams(request):
    '''collect valid parameters, check types'''
    
    params = dict()
    
    if request.method == "GET":
        form = PagerForm(request.GET)

        if form.is_valid():
            for k, v in form.cleaned_data.items():
                if (v == "") or (v == []) or (v is None):
                    continue
                elif not isinstance(v, list):
                    v = [v]
                params[k] = v

        # short-circuit if bad params encountered
        else:
            return None
        
    if "page_size" in params:
        try:
            params["page_size"] = int(params["page_size"][0])
        except ValueError:
            del params["page_size"]
    
    print(params)
    
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
        exclude = []


class SpeechClusterFilter(filters.FilterSet):
    
    work_id = filters.NumberFilter('speeches__work__id', distinct=True)
    work_title = filters.CharFilter('speeches__work__title', distinct=True)
    work_urn = filters.CharFilter('speeches__work__urn', distinct=True)
    work_wd = filters.CharFilter('speeches__work__wd', distinct=True)

    author_id = filters.NumberFilter('speeches__work__author__id', distinct=True)
    author_name = filters.CharFilter('speeches__work__author__name', distinct=True)
    author_wd = filters.CharFilter('speeches__work__author__wd', distinct=True)
    author_urn = filters.CharFilter('speeches__work__author__urn', distinct=True)

    spkr_id = filters.NumberFilter('speeches__spkr__char__id', distinct=True)
    spkr_name = filters.CharFilter('speeches__spkr__char__name', distinct=True)
    spkr_manto = filters.CharFilter('speeches__spkr__char__manto', distinct=True)
    spkr_wd = filters.CharFilter('speeches__spkr__char__wd', distinct=True)
    spkr_tt = filters.CharFilter('speeches__spkr__char__tt', distinct=True)    
    spkr_gender = filters.ChoiceFilter('speeches__spkr__char__gender', 
                    choices=Character.CharacterGender.choices, distinct=True)
    spkr_number = filters.ChoiceFilter('speeches__spkr__char__number',
                    choices=Character.CharacterNumber.choices, distinct=True)
    spkr_being = filters.ChoiceFilter('speeches__spkr__char__being',
                    choices=Character.CharacterBeing.choices, distinct=True)
    
    spkr_inst_id = filters.NumberFilter('speeches__spkr__id', distinct=True)
    spkr_inst_name = filters.CharFilter('speeches__spkr__name', distinct=True)
    spkr_inst_gender = filters.ChoiceFilter('speeches__spkr__gender', 
                    choices=Character.CharacterGender.choices, distinct=True)
    spkr_inst_number = filters.ChoiceFilter('speeches__spkr__number',
                    choices=Character.CharacterNumber.choices, distinct=True)
    spkr_inst_being = filters.ChoiceFilter('speeches__spkr__being',
                    choices=Character.CharacterBeing.choices, distinct=True)
    spkr_anon = filters.BooleanFilter('speeches__spkr__anon', distinct=True)

    addr_id = filters.NumberFilter('speeches__addr__char__id', distinct=True)
    addr_name = filters.CharFilter('speeches__addr__char__name', distinct=True)
    addr_manto = filters.CharFilter('speeches__addr__char__manto', distinct=True)
    addr_wd = filters.CharFilter('speeches__addr__char__wd', distinct=True)
    addr_tt = filters.CharFilter('speeches__addr__char__tt', distinct=True)    
    addr_gender = filters.ChoiceFilter('speeches__addr__char__gender', 
                    choices=Character.CharacterGender.choices, distinct=True)
    addr_number = filters.ChoiceFilter('speeches__addr__char__number',
                    choices=Character.CharacterNumber.choices, distinct=True)
    addr_being = filters.ChoiceFilter('speeches__addr__char__being',
                    choices=Character.CharacterBeing.choices, distinct=True)
                    
    addr_inst_id = filters.NumberFilter('speeches__addr__id', distinct=True)
    addr_inst_name = filters.CharFilter('speeches__addr__name', distinct=True)
    addr_inst_name = filters.CharFilter('speeches__addr__name', distinct=True)
    addr_inst_gender = filters.ChoiceFilter('speeches__addr__gender', 
                    choices=Character.CharacterGender.choices, distinct=True)
    addr_inst_number = filters.ChoiceFilter('speeches__addr__number',
                    choices=Character.CharacterNumber.choices, distinct=True)
    addr_inst_being = filters.ChoiceFilter('speeches__addr__being',
                    choices=Character.CharacterBeing.choices, distinct=True)
    addr_anon = filters.BooleanFilter('speeches__addr__anon', distinct=True)
    
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
    
    def get_serializer(self, *args, **kwargs):
        if self.request.query_params.get('min'):
            kwargs['fields'] = ['id']
        if 'depth' in self.request.query_params:
            depth = self.request.query_params['depth']
            m = re.fullmatch(r'\d+', depth)
            if m:
                kwargs['depth'] = int(depth)
        return super().get_serializer(*args, **kwargs)


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
    template_name = "speechdb/author_list.html"
    paginate_by = PAGE_SIZE
    
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        
        # form data
        context["text_form"] = TextForm(self.request.GET)
        context["pager_form"] = PagerForm(self.request.GET)
        
        return context

    def get_queryset(self):
        # collect user search params
        params = ValidateParams(self.request)    

        # construct query
        query = []
        
        # language
        if "lang" in params:
            q = Q()
            for lang in params["lang"]:
                q |= Q(work__lang=lang)
            query.append(q)
        
        # get query set
        qs = Author.objects.filter(*query).prefetch_related('work_set').distinct()
        
        for author in qs:
                works = list(author.work_set.all())
                author.work_count = len(works)
                author.langs = ", ".join(sorted(set(w.lang for w in works if w.lang)))
        
        # pagination
        if "page_size" in params:
            if params["page_size"] > 0:
                self.paginate_by = params["page_size"]
            else:
                self.paginate_by = qs.count() + 1        

        return qs


class AppWorkList(ListView):
    model = Work
    template_name = 'speechdb/work_list.html'
    paginate_by = PAGE_SIZE
    
    def get_queryset(self):
        # collect user search params
        params = ValidateParams(self.request)

        # construct query
        query = []
        
        # text properties
        if 'author_name' in params:
            q = Q()
            for author_name in params["author_name"]:
                q |= Q(instances__speeches__work__author__name=author_name)
                q |= Q(instances__addresses__work__author__name=author_name)
            query.append(q)


        if 'author_id' in params:
            q = Q()
            for pk in params["author_id"]:
                q |= Q(instances__speeches__work__author__pk=pk)
                q |= Q(instances__addresses__work__author__pk=pk)
            query.append(q)


        if 'author_pubid' in params:
            q = Q()
            for pubid in params["author_pubid"]:
                q |= Q(instances__speeches__work__author__public_id=pubid)
                q |= Q(instances__addresses__work__author__public_id=pubid)
            query.append(q)

        if 'work_title' in params:
            q = Q()
            for work_title in params["work_title"]:
                q |= Q(instances__speeches__work__title=work_title)
                q |= Q(instances__addresses__work__title=work_title)
            query.append(q)
            
        if 'lang' in params:
            q = Q()
            for lang in params["lang"]:
                q |= Q(instances__speeches__work__lang=lang)
                q |= Q(instances__addresses__work__lang=lang)
            query.append(q)

        # perform query
        qs = Work.objects.filter(*query).distinct().order_by('author', 'title')

        # annotate results
        qs = qs.annotate(
            Count('speech', distinct=True),
            Count('speech__spkr', distinct=True),
        )

        # pagination
        if 'page_size' in params:
            if params['page_size'] > 0:
                self.paginate_by = params['page_size']
            else:
                self.paginate_by = qs.count() + 1
          
        return qs


    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)

        # form data
        context['text_form'] = TextForm(self.request.GET)
        context['pager_form'] = PagerForm(self.request.GET)
        
        return context



class AppCharacterList(ListView):
    model = Character
    template_name = 'speechdb/character_list.html'
    paginate_by = PAGE_SIZE
        
    def get_queryset(self):
        
        # collect user search params
        params = ValidateParams(self.request)
                                
        # construct query
        query = []
        
        if "char_name" in params:
            q = Q()
            for name in params["char_name"]:
                q |= Q(name=name)
            query.append(q)
            
        if 'char_gender' in params:
            q = Q()
            for gender in params["char_gender"]:
                q |= Q(gender=gender)
            query.append(q)
        
        if 'char_being' in params:
            q = Q()
            for being in params["char_being"]:
                q |= Q(being=being)
            query.append(q)
            
        if 'char_number' in params:
            q = Q()
            for number in params["char_number"]:
                q |= Q(number=number)
            query.append(q)

        if 'char_manto' in params:
            q = Q()
            for manto in params["char_manto"]:
                q |= Q(manto=manto)
            query.append(q)

        if 'char_wd' in params:
            q = Q()
            for wd in params["wd"]:
                q |= Q(wd=wd)
            query.append(q)

        if 'char_tt' in params:
            q = Q()
            for tt in params["tt"]:
                q |= Q(tt=tt)
            query.append(q)

        # text properties
        if 'author_name' in params:
            q = Q()
            for author_name in params["author_name"]:
                q |= Q(instances__speeches__work__author__name=author_name)
                q |= Q(instances__addresses__work__author__name=author_name)
            query.append(q)

        if 'author_id' in params:
            q = Q()
            for author_pubid in params["author_id"]:
                q |= Q(instances__speeches__work__author__public_id=author_pubid)
                q |= Q(instances__addresses__work__author__public_id=author_pubid)
            query.append(q)

        if 'author_pk' in params:
            q = Q()
            for author_pk in params["author_pk"]:
                q |= Q(instances__speeches__work__author__pk=author_pk)
                q |= Q(instances__addresses__work__author__pk=author_pk)
            query.append(q)

        if 'work_title' in params:
            q = Q()
            for work_title in params["work_title"]:
                q |= Q(instances__speeches__work__title=work_title)
                q |= Q(instances__addresses__work__title=work_title)
            query.append(q)

        if 'work_id' in params:
            q = Q()
            for work_pubid in params["work_id"]:
                q |= Q(instances__speeches__work__public_id=work_pubid)
                q |= Q(instances__addresses__work__public_id=work_pubid)
            query.append(q)
            
        if 'work_pk' in params:
            q = Q()
            for work_pk in params["work_pk"]:
                q |= Q(instances__speeches__work__pk=work_pk)
                q |= Q(instances__addresses__work__pk=work_pk)
            query.append(q)

        if 'lang' in params:
            q = Q()
            for lang in params["lang"]:
                q |= Q(instances__speeches__work__lang=lang)
                q |= Q(instances__addresses__work__lang=lang)
            query.append(q)
        
        qs = Character.objects.filter(*query).distinct().order_by('name')
        
        # calculate some useful counts
        qs = qs.annotate(
            Count('instances__speeches', distinct=True),
            Count('instances__addresses', distinct=True),
        )
        
        # pagination
        if 'page_size' in params:
            if params['page_size'] > 0:
                self.paginate_by = params['page_size']
            else:
                self.paginate_by = qs.count() + 1        
        
        return qs


    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)

        # form data
        context['character_form'] = CharacterForm(self.request.GET)
        context['text_form'] = TextForm(self.request.GET)
        context["pager_form"] = PagerForm(self.request.GET)
       
        return context


class AppCharacterInstanceList(ListView):
    model = CharacterInstance
    template_name = 'speechdb/characterinstance_list.html'
    queryset = CharacterInstance.objects.all()
    paginate_by = PAGE_SIZE
    
    
    def get_queryset(self):
        
        # collect user search params
        params = ValidateParams(self.request)
                                
        # construct query
        query = []
        
        # instance properties
        if "inst_name" in params:
            q = Q()
            for name in params["inst_name"]:
                q |= Q(name=name)
            query.append(q)
            
        if 'inst_gender' in params:
            q = Q()
            for gender in params["inst_gender"]:
                q |= Q(gender=gender)
            query.append(q)
        
        if 'inst_being' in params:
            q = Q()
            for being in params["inst_being"]:
                q |= Q(being=being)
            query.append(q)
            
        if 'inst_number' in params:
            q = Q()
            for number in params["inst_number"]:
                q |= Q(number=number)
            query.append(q)
         
        if 'inst_anon' in params:
            q = Q()
            for anon in params["inst_anon"]:
                q |= Q(anon=anon)
            query.append(q)
        
        # character properties
        if "char_id" in params:
            q = Q()
            for char_pubid in params["char_id"]:
                q |= Q(char__public_id=char_pubid)
            query.append(q)

        if "char_pk" in params:
            q = Q()
            for char_pk in params["char_pk"]:
                q |= Q(char__public_pk=char_pk)
            query.append(q)

        if "char_name" in params:
            q = Q()
            for name in params["char_name"]:
                q |= Q(char__name=name)
            query.append(q)
            
        if 'char_gender' in params:
            q = Q()
            for gender in params["char_gender"]:
                q |= Q(char__gender=gender)
            query.append(q)
        
        if 'char_being' in params:
            q = Q()
            for being in params["char_being"]:
                q |= Q(char__being=being)
            query.append(q)
            
        if 'char_number' in params:
            q = Q()
            for number in params["char_number"]:
                q |= Q(char__number=number)
            query.append(q)
        
        if 'char_manto' in params:
            q = Q()
            for manto in params["char_manto"]:
                q |= Q(char__manto=manto)
            query.append(q)

        if 'char_wd' in params:
            q = Q()
            for wd in params["char_wd"]:
                q |= Q(char__wd=wd)
            query.append(q)

        if 'char_tt' in params:
            q = Q()
            for tt in params["char_tt"]:
                q |= Q(char__tt=tt)
            query.append(q)
            
        # text properties
        if 'author_id' in params:
            q = Q()
            for author_pubid in params["author_id"]:
                q |= Q(speeches__work__author__public_id=author_pubid)
                q |= Q(addresses__work__author__public_id=author_pubid)
            query.append(q)

        if 'author_pk' in params:
            q = Q()
            for author_pk in params["author_pk"]:
                q |= Q(speeches__work__author__pk=author_pk)
                q |= Q(addresses__work__author__pk=author_pk)
            query.append(q)

        if 'author_name' in params:
            q = Q()
            for author_name in params["author_name"]:
                q |= Q(speeches__work__author__name=author_name)
                q |= Q(addresses__work__author__name=author_name)
            query.append(q)

        if 'work_title' in params:
            q = Q()
            for work_title in params:
                q |= Q(speeches__work__title=work_title)
                q |= Q(addresses__work__title=work_title)
            query.append(q)

        if 'work_id' in params:
            q = Q()
            for work_pubid in params:
                q |= Q(speeches__work__public_id=work_pubid)
                q |= Q(addresses__work__public_id=work_pubid)
            query.append(q)
        
        if 'work_pk' in params:
            q = Q()
            for work_pk in params:
                q |= Q(speeches__work__pk=work_pk)
                q |= Q(addresses__work__pk=work_pk)
            query.append(q)
            
        if 'lang' in params:
            q = Q()
            for lang in params["lang"]:
                q |= Q(speeches__work__lang=lang)
                q |= Q(addresses__work__lang=lang)
            query.append(q)
        
        # perform query
        qs = CharacterInstance.objects.filter(*query).order_by('name')
        
        # calculate some useful counts
        qs = qs.annotate(
            Count('speeches', distinct=True),
            Count('addresses', distinct=True),
        )
        
        # pagination
        if 'page_size' in params:
            if params["page_size"] > 0:
                self.paginate_by = params["page_size"]
            else:
                self.paginate_by = qs.count() + 1
        
        return qs


    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        
        # form data
        context["character_form"] = CharacterForm(self.request.GET)
        context["instance_form"] = InstanceForm(self.request.GET)
        context["text_form"] = TextForm(self.request.GET)
        context["pager_form"] = PagerForm(self.request.GET)
                            
        return context


class SpeechQueryMixin:
    '''validate and assemble speech query params
        - designed to be reused by HTML and CSV views
    '''
        
    @property
    def params(self):
        if not hasattr(self, "_params"):
            self._params = ValidateParams(self.request)
    
        return self._params
    
    
    def speech_queryset(self):
        
        # collect user search params
        params = self.params
        
        # short-circuit if search params are malformed
        if params is None:
            return Speech.objects.none()
                            
        # initial set of objects plus annotations
        qs = Speech.objects.annotate(Count('cluster__speeches'))
        
        # construct query
        query = []
        
        #
        # speaker properties
        # 
        
        # speaker character public id
        if "spkr_char_id" in params:
            q = Q()
            for pubid in params["spkr_char_id"]:
                q |= Q(spkr__char__public_id=pubid)
            query.append(q)

        # speaker character id
        if "spkr_char_pk" in params:
            q = Q()
            for pk in params["spkr_char_pk"]:
                q |= Q(spkr__char__pk=pk)
            query.append(q)

        # speaker character name
        if "spkr_char_name" in params:
            q = Q()
            for name in params["spkr_char_name"]:
                q |= Q(spkr__char__name=name)
            query.append(q)
            
        # speaker character being
        if "spkr_char_being" in params:
            q = Q()
            for being in params["spkr_char_being"]:
                q |= Q(spkr__char__being=being)
            query.append(q)

        # speaker character gender
        if "spkr_char_gender" in params:
            q = Q()
            for gender in params["spkr_char_gender"]:
                q |= Q(spkr__char__gender=gender)
            query.append(q)
            
        # speaker character number
        if "spkr_char_number" in params:
            q = Q()
            for number in params["spkr_char_number"]:
                q |= Q(spkr__char__number=number)
            query.append(q)
            
        # speaker manto
        if "spkr_char_manto" in params:
            q = Q()
            for manto in params["spkr_char_manto"]:
                q |= Q(spkr__char__manto=manto)
            query.append(q)

        # speaker wikidata
        if "spkr_char_wd" in params:
            q = Q()
            for wd in params["spkr_char_wd"]:
                q |= Q(spkr__char__wd=wd)
            query.append(q)

        # speaker topostext
        if "spkr_char_tt" in params:
            q = Q()
            for tt in params["spkr_char_tt"]:
                q |= Q(spkr__char__tt=tt)
            query.append(q)
            
        # speaker instance public id
        if "spkr_inst_id" in params:
            q = Q()
            for pubid in params["spkr_inst_id"]:
                q |= Q(spkr__public_id=pubid)
            query.append(q)

        # speaker instance pk
        if "spkr_inst_pk" in params:
            q = Q()
            for pk in params["spkr_inst_pk"]:
                q |= Q(spkr__pk=pk)
            query.append(q)
        
        # speaker instance name
        if "spkr_inst_name" in params:
            q = Q()
            for name in params["spkr_inst_name"]:
                q |= Q(spkr__name=name)
            query.append(q)
            
        # speaker instance being
        if "spkr_inst_being" in params:
            q = Q()
            for being in params["spkr_inst_being"]:
                q |= Q(spkr__being=being)
            query.append(q)

        # speaker instance gender
        if "spkr_inst_gender" in params:
            q = Q()
            for gender in params["spkr_inst_gender"]:
                q |= Q(spkr__gender=gender)
            query.append(q)

        # speaker instance number
        if "spkr_inst_number" in params:
            q = Q()
            for number in params["spkr_inst_number"]:
                q |= Q(spkr__number=number)
            query.append(q)
        
        # speaker disguised
        if "spkr_disguised" in params:
            if len(params["spkr_disguised"]) > 0:
                query.append(Q(spkr__disguise__isnull=not(params["spkr_disguised"][0])))
            
        #
        # addressee properties
        #
                    
        # addressee character public id
        if "addr_char_id" in params:
            q = Q()
            for puid in params["addr_char_id"]:
                q |= Q(addr__char__public_id=pubid)
            query.append(q)

        # addressee character pk
        if "addr_char_pk" in params:
            q = Q()
            for pk in params["addr_char_pk"]:
                q |= Q(addr__char__pk=pk)
            query.append(q)

        # addressee character name
        if "addr_char_name" in params:
            q = Q()
            for name in params["addr_char_name"]:
                q |= Q(addr__char__name=name)
            query.append(q)
            
        # addressee character being
        if "addr_char_being" in params:
            q = Q()
            for being in params["addr_char_being"]:
                q |= Q(addr__char__being=being)
            query.append(q)

        # addressee character gender
        if "addr_char_gender" in params:
            q = Q()
            for gender in params["addr_char_gender"]:
                q |= Q(addr__char__gender=gender)
            query.append(q)
            
        # addressee character number
        if "addr_char_number" in params:
            q = Q()
            for number in params["addr_char_number"]:
                q |= Q(addr__char__number=number)
            query.append(q)
            
        # addressee manto
        if "addr_char_manto" in params:
            q = Q()
            for manto in params["addr_char_manto"]:
                q |= Q(addr__char__manto=manto)
            query.append(q)

        # addressee wikidata
        if "addr_char_wd" in params:
            q = Q()
            for wd in params["addr_char_wd"]:
                q |= Q(addr__char__wd=wd)
            query.append(q)

        # addressee topostext
        if "addr_char_tt" in params:
            q = Q()
            for tt in params["addr_char_tt"]:
                q |= Q(addr__char__tt=tt)
            query.append(q)
            
        # addressee instance public id
        if "addr_inst_id" in params:
            q = Q()
            for pubid in params["addr_inst_id"]:
                q |= Q(addr__public_id=pubid)
            query.append(q)

        # addressee instance pk
        if "addr_inst_pk" in params:
            q = Q()
            for pk in params["addr_inst_pk"]:
                q |= Q(addr__pk=pk)
            query.append(q)
        
        # addressee instance name
        if "addr_inst_name" in params:
            q = Q()
            for name in params["addr_inst_name"]:
                q |= Q(addr__name=name)
            query.append(q)
            
        # addressee instance being
        if "addr_inst_being" in params:
            q = Q()
            for being in params["addr_inst_being"]:
                q |= Q(addr__being=being)
            query.append(q)

        # addressee instance gender
        if "addr_inst_gender" in params:
            q = Q()
            for gender in params["addr_inst_gender"]:
                q |= Q(addr__gender=gender)
            query.append(q)

        # addressee instance number
        if "addr_inst_number" in params:
            q = Q()
            for number in params["addr_inst_number"]:
                q |= Q(addr__number=number)
            query.append(q)
        
        # addressee disguised
        if "addr_disguised" in params:
            if len(params["addr_disguised"]) > 0:
                query.append(Q(addr__disguise__isnull=not(params["addr_disguised"][0])))
                     
        #
        # speech properties
        # 

        # cluster public id
        if "cluster_id" in params:
            q = Q()
            for pubid in params["cluster_id"]:
                q |= Q(cluster__public_id=pubid)
            query.append(q)

        # cluster pk
        if "cluster_pk" in params:
            q = Q()
            for pk in params["cluster_pk"]:
                q |= Q(cluster__pk=pk)
            query.append(q)
        
        # cluster type
        if "type" in params:
            q = Q()
            for type_ in params["type"]:
                q |= Q(type=type_)
            query.append(q)
        
        # cluster part
        if "part" in params:
            q = Q()
            for part in params["part"]:
                q |= Q(part=part)
            query.append(q)
        
        # total parts in cluster
        if "n_parts" in params:
            q = Q()
            for n in params["n_parts"]:
                q |= Q(cluster__speeches__count=n)
            query.append(q)

        # embedded level
        if "level" in params:
            q = Q()
            for level in params["level"]:
                q |= Q(level=level)
            query.append(q)
            
        # speech tags
        if "tags" in params:
            q = Q()
            for tag in params["tags"]:
                q |= Q(tags__type=tag)
            query.append(q)
        
        #
        # work properties
        #
        
        # work public id
        if "work_id" in params:
            q = Q()
            for pubid in params["work_id"]:
                q |= Q(work__public_id=pubid)
            query.append(q)

        # work pk
        if "work_pk" in params:
            q = Q()
            for pk in params["work_pk"]:
                q |= Q(work__pk=pk)
            query.append(q)
        
        # work title
        if "work_title" in params:
            q = Q()
            for title in params["work_title"]:
                q |= Q(work__title=title)
            query.append(q)
            
        # author public id
        if "auth_id" in params:
            q = Q()
            for pubid in params["auth_id"]:
                q |= Q(work__author__public_id=pubid)
            query.append(q)

        # author pk
        if "auth_pk" in params:
            q = Q()
            for pk in params["auth_pk"]:
                q |= Q(work__author__pk=pk)
            query.append(q)
            
        # author name
        if "author_name" in params:
            q = Q()
            for name in params["author_name"]:
                q |= Q(work__author__name=name)
            query.append(q)
            
        # language
        if "lang" in params:
            q = Q()
            for lang in params["lang"]:
                q |= Q(work__lang=lang)
            query.append(q)

        # execute query
        qs = qs.filter(*query).distinct().order_by("work", "seq")
        return qs
            

class AppSpeechList(SpeechQueryMixin, ListView):
    model = Speech
    template_name = 'speechdb/speech_list.html'
    paginate_by = PAGE_SIZE
    ordering = ['work', 'seq']

    def get_queryset(self):
        return self.speech_queryset()
    
    def get_paginate_by(self, qs):
        if self.params is None:
            ps = PAGE_SIZE
        else:
            ps = self.params.get("page_size", PAGE_SIZE)

        if ps > 0:
            return ps
    
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)

        # form data
        context["spkr_character_form"] = CharacterForm(self.request.GET, prefix="spkr")
        context["spkr_instance_form"] = InstanceForm(self.request.GET, prefix="spkr")
        context["addr_character_form"] = CharacterForm(self.request.GET, prefix="addr")
        context["addr_instance_form"] = InstanceForm(self.request.GET, prefix="addr")  
        context["speech_form"] = SpeechForm(self.request.GET)      
        context["text_form"] = TextForm(self.request.GET)
        context["pager_form"] = PagerForm(self.request.GET)

        # CTS reader
        context['reader'] = CTS_READER
        
        return context
    

class AppSpeechCSV(SpeechQueryMixin, View):
    '''export speech list as a CSV text file'''
    
    filename = "speeches.csv"

    def get(self, request):
        qs = self.speech_queryset()

        if qs is None or not qs.exists():  # optional; speech_queryset can return none()
            qs = []

        response = HttpResponse(
            content_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{self.filename}"'},
        )

        writer = csv.writer(response)
        writer.writerow(["work", "first_line", "last_line", "speaker", "addressee"])  # headers

        for s in qs:
            writer.writerow([s.work.title, s.l_fi, s.l_la, s.get_spkr_str(), s.get_addr_str()])

        return response
        
        
class AppSpeechClusterList(ListView):
    model = SpeechCluster
    template_name = 'speechdb/speechcluster_list.html'
    paginate_by = PAGE_SIZE
    
    def get_queryset(self):
        # collect user search params
        params = ValidateParams(self.request)
        
        # initial set of objects plus annotations
        qs = SpeechCluster.objects.annotate(Count('speeches'))
                
        # construct query
        query = []
        
        #
        # any participant
        #
        
        # any participant by character public id
        if "char_id" in params:
            q = Q()
            for pubid in params["char_id"]:
                q |= Q(speeches__spkr__char__public_id=pubid)
                q |= Q(speeches__addr__char__public_id=pubid)
            query.append(q)

        # any participant by character id
        if "char_pk" in params:
            q = Q()
            for pk in params["char_pk"]:
                q |= Q(speeches__spkr__char__pk=pk)
                q |= Q(speeches__addr__char__pk=pk)
            query.append(q)
        
        # any participant by character name
        if "char_name" in params:
            q = Q()
            for name in params["char_name"]:
                q |= Q(speeches__spkr__char__name=name)
                q |= Q(speeches__addr__char__name=name)
            query.append(q)

        # any participant by character being
        if "char_being" in params:
            q = Q()
            for being in params["char_being"]:
                q |= Q(speeches__spkr__char__being=being)
                q |= Q(speeches__addr__char__being=being)
            query.append(q)

        # any participant by character gender
        if "char_gender" in params:
            q = Q()
            for gender in params["gender"]:
                q |= Q(speeches__spkr__char__gender=gender) 
                q |= Q(speeches__addr__char__gender=gender)
            query.append(q)
            
        # any participant by instance public id
        if "inst_id" in params:
            q = Q()
            for pubid in params["inst_id"]:
                q |= Q(speeches__spkr__public_id=pubid)
                q |= Q(speeches__addr__public_id=pubid)
            query.append(q)

        # any participant by instance pk
        if "inst_pk" in params:
            q = Q()
            for pk in params["inst_pk"]:
                q |= Q(speeches__spkr__pk=pk)
                q |= Q(speeches__addr__pk=pk)
            query.append(q)
        
        # any participant by instance name
        if "inst_name" in params:
            q = Q()
            for name in params["inst_name"]:
                q |= Q(speeches__spkr__name=name)
                q |= Q(speeches__addr__name=name)
            query.append(q)

        # any participant by instance being
        if "inst_being" in params:
            q = Q()
            for being in params["char_being"]:
                q |= Q(speeches__spkr__being=being)
                q |= Q(speeches__addr__being=being)
            query.append(q)

        # any participant by instance gender
        if "inst_gender" in params:
            q = Q()
            for gender in params["gender"]:
                q |= Q(speeches__spkr__gender=gender)
                q |= Q(speeches__addr__gender=gender)
            query.append(q)
                    
        # any participant disguised
        if "disguised" in params:
            q = Q()
            for disg in params["disguised"]:
                q |= Q(speeches__spkr__disguise__isnull=not(disg))
                q |= Q(speeches__addr__disguise__isnull=not(disg))                
            query.append()
                    
                    
        #
        # speaker
        #
                    
        # speaker by character public id
        if "spkr_char_id" in params:
            q = Q()
            for pubid in params["spkr_char_id"]:
                q |= Q(speeches__spkr__char__public_id=pubid)
            query.append(q)

        # speaker by character pk
        if "spkr_char_pk" in params:
            q = Q()
            for pk in params["spkr_char_pk"]:
                q |= Q(speeches__spkr__char__pk=pk)
            query.append(q)
                    
        # speaker by character name
        if "spkr_char_name" in params:
            q = Q()
            for name in params["spkr_char_name"]:
                q |= Q(speeches__spkr__char__name=name)
            query.append(q)

        # speaker by character being
        if "spkr_char_being" in params:
            q = Q()
            for being in params["spkr_char_being"]:
                q |= Q(speeches__spkr__char__being=being)
            query.append(q)

        # speaker by character number
        if "spkr_char_number" in params:
            q = Q()
            for number in params["spkr_char_number"]:
                q |= Q(speeches__spkr__char__number=number)
            query.append(q)

        # speaker by character gender
        if "spkr_gender" in params:
            q = Q()
            for gender in params["gender"]:
                q |= Q(speeches__spkr__char__gender=gender)
            query.append(q)
        
        # speaker by instance id
        if "spkr_inst_id" in params:
            q = Q()
            for id in params["spkr_inst_id"]:
                q |= Q(speeches__spkr__id=id)
            query.append(q)
        
        # speaker by instance name
        if "spkr_inst_name" in params:
            q = Q()
            for name in params["spkr_inst_name"]:
                q |= Q(speeches__spkr__name=name)
            query.append(q)
            
        # speaker instance being
        if "spkr_inst_being" in params:
            q = Q()
            for being in params["spkr_inst_being"]:
                q |= Q(speeches__spkr__being=being)
            query.append(q)

        # speaker instance gender
        if "spkr_inst_gender" in params:
            q = Q()
            for gender in params["spkr_inst_gender"]:
                q |= Q(speeches__spkr__gender=gender)
            query.append(q)

        # speaker instance number
        if "spkr_inst_number" in params:
            q = Q()
            for number in params["spkr_inst_number"]:
                q |= Q(speeches__spkr__number=number)
            query.append(q)
        
        # speaker disguised
        if "spkr_disguised" in params:
            if len(params["spkr_disguised"]) > 0:
                query.append(Q(speeches__spkr__disguise__isnull=not(params["spkr_disguised"][0])))
        
        #
        # addressee
        #
        
        # addressee by character public id
        if "addr_char_id" in params:
            q = Q()
            for pubid in params["addr_char_id"]:
                q |= Q(speeches__addr__char__public_id=pubid)
            query.append(q)
                    
        # addressee by character pk
        if "addr_char_pk" in params:
            q = Q()
            for id in params["addr_char_pk"]:
                q |= Q(speeches__addr__char__pk=pk)
            query.append(q)

        # addressee by character name
        if "addr_char_name" in params:
            q = Q()
            for name in params["addr_char_name"]:
                q |= Q(speeches__addr__char__name=name)
            query.append(q)

        # addressee by character being
        if "addr_char_being" in params:
            q = Q()
            for being in params["addr_char_being"]:
                q |= Q(speeches__addr__char__being=being)
            query.append(q)

        # addressee by character number
        if "addr_char_number" in params:
            q = Q()
            for number in params["addr_char_number"]:
                q |= Q(speeches__addr__char__number=number)
            query.append(q)

        # addressee by character gender
        if "addr_gender" in params:
            q = Q()
            for gender in params["gender"]:
                q |= Q(speeches__addr__char__gender=gender)
            query.append(q)
        
        # addressee by instance public id
        if "addr_inst_id" in params:
            q = Q()
            for pubid in params["addr_inst_id"]:
                q |= Q(speeches__addr__public_id=pubid)
            query.append(q)

        # addressee by instance pk
        if "addr_inst_pk" in params:
            q = Q()
            for pk in params["addr_inst_pk"]:
                q |= Q(speeches__addr__pk=pk)
            query.append(q)
        
        # addressee by instance name
        if "addr_inst_name" in params:
            q = Q()
            for name in params["addr_inst_name"]:
                q |= Q(speeches__addr__name=name)
            query.append(q)
            
        # addressee instance being
        if "addr_inst_being" in params:
            q = Q()
            for being in params["addr_inst_being"]:
                q |= Q(speeches__addr__being=being)
            query.append(q)

        # addressee instance gender
        if "addr_inst_gender" in params:
            q = Q()
            for gender in params["addr_inst_gender"]:
                q |= Q(speeches__addr__gender=gender)
            query.append(q)

        # addressee instance number
        if "addr_inst_number" in params:
            q = q()
            for number in params["addr_inst_number"]:
                q |= Q(speeches__addr__number=number)
            query.append(q)
        
        # addressee disguised
        if "addr_disguised" in params:
            if len(params["addr_disguised"]) > 0:
                query.append(Q(speeches__addr__disguise__isnull=not(params["addr_disguised"][0])))

        #
        # speech properties
        #

        # cluster public id
        if "cluster_id" in params:
            q = Q()
            for pubid in params["cluster_id"]:
                q |= Q(public_id=pubid)
            query.append(q)

        # cluster id
        if "cluster_pk" in params:
            q = Q()
            for pk in params["cluster_pk"]:
                q |= Q(pk=pk)
            query.append(q)
                        
        # turns in cluster
        if "n_parts" in params:
            q = Q()
            for n in params["n_parts"]:
                q |= Q(speeches__count=n)
            query.append(q)

        # turn type
        if "turn_type" in params:
            q = Q()
            for type_ in params["cluster_type"]:
                q |= Q(speeches__type=type_)
            query.append(q)
            
        # embedded level
        if "level" in params:
            q = Q()
            for level in params["level"]:
                q |= Q(speeches__level=level)
            query.append(q)

        # speech tags
        if "tags" in params:
            q = Q()
            for tag in params["tags"]:
                q |= Q(speeches__tags__type=tag)
            query.append(q)
        
        #
        # work properties
        #
        
        # work public id
        if "work_id" in params:
            q = Q()
            for pubid in params["work_id"]:
                q |= Q(speeches__work__public_id=pubid)
            query.append(q)

        # work pk
        if "work_pk" in params:
            q = Q()
            for id in params["work_pk"]:
                q |= Q(speeches__work__pk=pk)
            query.append(q)
        
        # work title
        if "work_title" in params:
            q = Q()
            for title in params["work_title"]:
                q |= Q(speeches__work__title=title)
            query.append(q)
            
        # author public id
        if "auth_pubid" in params:
            q = Q()
            for pubid in params["auth_pubid"]:
                q |= Q(speeches__work__author__public_id=pubid)
            query.append(q)

        # author pk
        if "auth_id" in params:
            q = Q()
            for pk in params["auth_id"]:
                q |= Q(speeches__work__author__pk=pk)
            query.append(q)
            
        # author name
        if "auth_name" in params:
            q = Q()
            for name in params["auth_name"]:
                q |= Q(speeches__work__author__name=name)
            query.append(q)
            
        # language
        if "lang" in params:
            q = Q()
            for lang in params["lang"]:
                q |= Q(speeches__work__lang=lang)
            query.append(q)        
                
        # execute query
        qs = qs.filter(*query).distinct()
        qs = qs.order_by('seq')

        # pagination
        if "page_size" in params:
            if params["page_size"] > 0:
                self.paginate_by = params["page_size"]
            else:
                self.paginate_by = qs.count() + 1
         
        return qs
    
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)

        # add useful info
        context["spkr_character_form"] = CharacterForm(self.request.GET, prefix="spkr")
        context["spkr_instance_form"] = InstanceForm(self.request.GET, prefix="spkr")
        context["addr_character_form"] = CharacterForm(self.request.GET, prefix="addr")
        context["addr_instance_form"] = InstanceForm(self.request.GET, prefix="addr")  
        context["speech_form"] = SpeechForm(self.request.GET)      
        context["text_form"] = TextForm(self.request.GET)
        context["pager_form"] = PagerForm(self.request.GET)
        
        return context

class AppAuthorDetail(DetailView):
    model = Author
    template_name = "speechdb/author_detail.html"
    context_object_name = "author"
    slug_field = "public_id"
    slug_url_kwarg = "public_id"


class AppWorkDetail(DetailView):
    model = Work
    template_name = "speechdb/work_detail.html"
    context_object_name = "work"
    slug_field = "public_id"
    slug_url_kwarg = "public_id"

    
class AppSpeechDetail(DetailView):
    model = Speech
    template_name = "speechdb/speech_detail.html"
    context_object_name = "speech"
    slug_field = "public_id"
    slug_url_kwarg = "public_id"


    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # add useful info
        context['reader'] = CTS_READER
                
        return context


class AppCharacterInstanceDetail(DetailView):
    model = CharacterInstance
    template_name = 'speechdb/characterinstance_detail.html'
    context_object_name = 'inst'
    slug_field = "public_id"
    slug_url_kwarg = "public_id"
    
    
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
    slug_field = "public_id"
    slug_url_kwarg = "public_id"
    
    
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # add useful info
        context['reader'] = CTS_READER
        
        return context


class AppSpeechClusterDetail(DetailView):
    model = SpeechCluster
    template_name = 'speechdb/speechcluster_detail.html'
    context_object_name = 'cluster'
    slug_field = "public_id"
    slug_url_kwarg = "public_id"

    
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