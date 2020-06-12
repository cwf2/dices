from django.contrib import admin
from .models import Author, Work, Character, CharacterInstance, Speech

admin.site.register(Author)
admin.site.register(Work)
admin.site.register(Character)
admin.site.register(CharacterInstance)
admin.site.register(Speech)
