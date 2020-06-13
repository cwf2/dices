from django.shortcuts import render
from django.http import HttpResponse
from .models import Character

def index(request):
    return HttpResponse(render(request, 'speechdb/index.html'))

def characters(request):
    context = {'characters': Character.objects.all()}
    return HttpResponse(render(request, 'speechdb/characters.html', context))

def speech(request, speech_id):
    return HttpResponse(f"You're looking at speech {speech_id}.")
    

def character(request, character_id):
    return HttpResponse(f"You're looking at character {character_id}.")

