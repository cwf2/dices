from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from .models import Character, Speech, SpeechCluster

CTS_READER = 'https://scaife.perseus.org/reader/'

def index(request):
    return HttpResponse(render(request, 'speechdb/index.html'))

def characters(request):
    context = {'characters': Character.objects.all()}
    return render(request, 'speechdb/characters.html', context)
    
def clusters(request):
    context = {'clusters': SpeechCluster.objects.all(), 'reader':CTS_READER}
    return render(request, 'speechdb/clusters.html', context)

def speeches(request):
    context = {'speeches': Speech.objects.all(), 'reader':CTS_READER}
    return render(request, 'speechdb/speeches.html', context)
