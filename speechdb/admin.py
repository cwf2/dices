from django.contrib import admin
from .models import Author, Work, Character, CharacterInstance, Speech, SpeechCluster, SpeechTag


class BaseAdmin(admin.ModelAdmin):
    list_per_page = 2000


@admin.register(Author)
class AuthorAdmin(BaseAdmin):
    list_display = ['name', 'urn', 'wd']
    search_fields = ['name', 'urn']

@admin.register(Work)
class WorkAdmin(BaseAdmin):
    list_display = ['title', 'author', 'lang']
    list_filter = ['lang', 'author']
    search_fields = ['title', 'author__name', 'urn']
    autocomplete_fields = ['author']

@admin.register(Character)
class CharacterAdmin(BaseAdmin):
    list_display = ['name', 'being', 'gender', 'number']
    list_filter = ['being', 'gender', 'number']
    search_fields = ['name', 'manto', 'wd']

@admin.register(CharacterInstance)
class CharacterInstanceAdmin(BaseAdmin):
    list_display = ['name', 'char', 'context', 'being', 'gender']
    list_filter = ['being', 'gender', 'number', 'anon']
    search_fields = ['name', 'char__name', 'context']
    autocomplete_fields = ['char']

@admin.register(Speech)
class SpeechAdmin(BaseAdmin):
    list_display = ['__str__', 'get_speakers', 'get_addressees', 'type', 'l_fi', 'l_la']
    list_filter = ['type', 'work', 'work__lang', 'level']
    search_fields = ['work__title', 'work__author__name', 'spkr__name', 'spkr__char__name', 'addr__name', 'l_fi']
    autocomplete_fields = ['work', 'cluster']
    filter_horizontal = ['spkr', 'addr']

    @admin.display(description='Speakers')
    def get_speakers(self, obj):
        return ', '.join(s.name for s in obj.spkr.all())

    @admin.display(description='Addressees')
    def get_addressees(self, obj):
        return ', '.join(a.name for a in obj.addr.all())

@admin.register(SpeechCluster)
class SpeechClusterAdmin(BaseAdmin):
    list_display = ['public_id', 'seq']
    search_fields = ['public_id']

@admin.register(SpeechTag)
class SpeechTagAdmin(BaseAdmin):
    list_display = ['speech', 'type', 'doubt']
    list_filter = ['type', 'doubt']
    search_fields = ['speech__work__title']
    autocomplete_fields = ['speech']
