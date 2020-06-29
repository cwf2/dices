from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Character, Speech, SpeechCluster, Work

CTS_READER = 'https://scaife.perseus.org/reader/'

def index(request):
    context = {
        'works': Work.objects.all(),
        'characters': Character.objects.all(), 
        'speech_types': SpeechCluster.speech_type_choices,
    }
    return render(request, 'speechdb/search.html', context)

def characters(request):
    page_size = int(request.GET.get('n', 25))
    page_num = int(request.GET.get('page', 1))
    paged_results = Paginator(Character.objects.all(), page_size)
    page_nos = list(range(max(1, page_num-2), min(page_num+2, paged_results.num_pages)))
    context = {
        'page': paged_results.get_page(page_num),
        'page_nos': page_nos,
    }
    return render(request, 'speechdb/characters.html', context)
    
def clusters(request):
    page_size = int(request.GET.get('n', 25))
    page_num = int(request.GET.get('page', 1))
    paged_results = Paginator(SpeechCluster.objects.all(), page_size)
    page_nos = list(range(max(1, page_num-2), min(page_num+2, paged_results.num_pages)))
    context = {
        'page': paged_results.get_page(page_num),
        'page_nos': page_nos,
        'reader':CTS_READER,
    }
    return render(request, 'speechdb/clusters.html', context)

def speeches(request):
    page_size = int(request.GET.get('n', 25))
    page_num = int(request.GET.get('page', 1))
    paged_results = Paginator(Speech.objects.all(), page_size)
    page_nos = list(range(max(1, page_num-2), min(page_num+2, paged_results.num_pages)))
    context = {
        'page': paged_results.get_page(page_num),
        'page_nos': page_nos,
        'reader':CTS_READER,
    }
    return render(request, 'speechdb/speeches.html', context)
    
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
    paged_results = Paginator(Speech.objects.all(), page_size)
    page_nos = list(range(max(1, page_num-2), min(page_num+2, paged_results.num_pages)))
    
    # render template
    context = {
        'page': paged_results.get_page(page_num),
        'page_nos': page_nos,
        'reader':CTS_READER,
    }
    
    return render(request, 'speechdb/speeches.html', context)
    
