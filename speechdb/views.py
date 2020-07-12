from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.generic import ListView, DetailView
from django_filters.views import FilterView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from django_filters import rest_framework as filters
from .models import Author, Work, Character, CharacterInstance, Speech, SpeechCluster
from .serializers import AuthorSerializer, WorkSerializer, CharacterSerializer, CharacterInstanceSerializer, SpeechSerializer, SpeechClusterSerializer

CTS_READER = 'https://scaife.perseus.org/reader/'
PAGE_SIZE = 25


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


class AppCharacterInstanceList(ListView):
    model = CharacterInstance
    template_name = 'speechdb/characterinstance_list.html'
    queryset = CharacterInstance.objects.all()
    paginate_by = PAGE_SIZE


class AppSpeechList(ListView):
    model = Speech
    template_name = 'speechdb/speech_list.html'
    queryset = Speech.objects.all()
    paginate_by = PAGE_SIZE
    
    # def get_queryset(self):
    #     qs = self.model.objects.all()
    #     filtered_list = AppSpeechFilter(self.request.GET, queryset=qs)
    #     return filtered_list.qs
        
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # add useful info
        context['reader'] = CTS_READER
        return context

class AppSpeechClusterList(ListView):
    model = SpeechCluster
    template_name = 'speechdb/speechcluster_list.html'
    queryset = SpeechCluster.objects.all()
    paginate_by = PAGE_SIZE


#
# old, function-based views
#

def index(request):
    context = {
        'works': Work.objects.all(),
        'characters': Character.objects.all(), 
        'speech_types': SpeechCluster.speech_type_choices,
    }
    return render(request, 'speechdb/search.html', context)


def search(request):
    '''Perform a search'''
    
    # sanitize inputs
    valid_params = [
        ('spkr_id', int),
        ('addr_id', int),
        ('cluster_id', int),
        ('cluster_type', str),
        ('work_id', int),
    ]
    
    params = {}
    
    for param, vtype in valid_params:
        if param in request.GET:
            val = request.GET[param][:256].strip()
            if val != '':
                try:
                    params[param] = vtype(val)
                except ValueError:
                    pass
    
    # construct query
    query = []
    
    # speaker by id
    if 'spkr_id' in params:
        query.append(Q(spkr__char=params['spkr_id']) | Q(spkr__disg=params['spkr_id']))
    
    # addressee by id
    if 'addr_id' in params:
        query.append(Q(addr__char=params['addr_id']) | Q(addr__disg=params['addr_id']))
    
    if 'cluster_id' in params:
        query.append(Q(cluster__pk=params['cluster_id']))
    
    if 'cluster_type' in params:
        query.append(Q(cluster__type=params['cluster_type']))
    
    if 'work_id' in params:
        query.append(Q(cluster__work__pk=params['work_id']))
    
    # run query
    results = Speech.objects.filter(*query)
    
    # pager
    page_size = int(request.GET.get('n', 25))
    page_num = int(request.GET.get('page', 1))
    paged_results = Paginator(results, page_size)
    page_nos = list(range(max(1, page_num-2), min(page_num+2, paged_results.num_pages)))
    
    # render template
    context = {
        'page': paged_results.get_page(page_num),
        'page_nos': page_nos,
        'reader':CTS_READER,
    }
    
    return render(request, 'speechdb/speeches.html', context)
    
