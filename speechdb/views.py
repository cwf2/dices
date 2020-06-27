from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.db.models import Q
from .models import Character, Speech, SpeechCluster

CTS_READER = 'https://scaife.perseus.org/reader/'

def index(request):
    context = {
        'characters': Character.objects.all(), 
        'speech_types': SpeechCluster.speech_types,
    }
    return render(request, 'speechdb/search.html', context)

def characters(request):
    context = {'characters': Character.objects.all()}
    return render(request, 'speechdb/characters.html', context)
    
def clusters(request):
    context = {'clusters': SpeechCluster.objects.all(), 'reader':CTS_READER}
    return render(request, 'speechdb/clusters.html', context)

def speeches(request):
    context = {'speeches': Speech.objects.all(), 'reader':CTS_READER}
    return render(request, 'speechdb/speeches.html', context)
    
def search(request):
    '''Perform a search'''
    
    # sanitize inputs
    valid_params = [
        ('spkr_id', int),
        ('addr_id', int),
        ('cluster_id', int),
        ('cluster_type', str),
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
    
    # run query
    results = Speech.objects.filter(*query)
    
    # render template
    context = {'speeches': results, 'reader': CTS_READER}
    return render(request, 'speechdb/speeches.html', context)
    
