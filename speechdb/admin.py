from django.contrib import admin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import path
from .models import Author, Work, Character, CharacterInstance, Speech, SpeechCluster, SpeechTag


class BaseAdmin(admin.ModelAdmin):
    list_per_page = 2000


@admin.register(Author)
class AuthorAdmin(BaseAdmin):
    readonly_fields = ["public_id"]
    list_display = ['name', 'urn', 'wd']
    search_fields = ['name', 'urn']

@admin.register(Work)
class WorkAdmin(BaseAdmin):
    readonly_fields = ["public_id"]
    list_display = ['title', 'author', 'lang']
    list_filter = ['lang', 'author']
    search_fields = ['title', 'author__name', 'urn']
    autocomplete_fields = ['author']

@admin.register(Character)
class CharacterAdmin(BaseAdmin):
    readonly_fields = ["public_id"]
    list_display = ['name', 'being', 'gender', 'number']
    list_filter = ['being', 'gender', 'number']
    search_fields = ['name', 'manto', 'wd']

@admin.register(CharacterInstance)
class CharacterInstanceAdmin(BaseAdmin):
    readonly_fields = ["public_id"]
    list_display = ['name', 'char', 'context', 'being', 'gender', "changed"]
    list_filter = ['being', 'gender', 'number', 'anon', "changed"]
    search_fields = ['name', 'char__name', 'context']
    autocomplete_fields = ['char']

    class Media:
        js = ['speechdb/admin_characterinstance.js']

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        context = request.GET.get('context')
        if context:
            initial['context'] = context
        return initial

    def get_urls(self):
        custom_urls = [
            path(
                'character-defaults/<int:char_id>/',
                self.admin_site.admin_view(self.character_defaults),
                name='speechdb_characterinstance_character_defaults',
            ),
        ]
        return custom_urls + super().get_urls()

    def character_defaults(self, request, char_id):
        '''Return a character's being/gender/number, for autopopulating a new instance'''
        char = get_object_or_404(Character, pk=char_id)
        return JsonResponse({
            'being': char.being,
            'gender': char.gender,
            'number': char.number,
        })

class SpeechTagInline(admin.TabularInline):
    model = SpeechTag
    extra = 1
    fields = ['type', 'doubt', 'notes']


@admin.register(Speech)
class SpeechAdmin(BaseAdmin):
    readonly_fields = ["public_id"]
    list_display = ['__str__', 'get_speakers', 'get_addressees', 'type', 'l_fi', 'l_la']
    list_filter = ['type', 'work', 'work__lang', 'level']
    search_fields = ['work__title', 'work__author__name', 'spkr__name', 'spkr__char__name', 'addr__name', 'l_fi']
    autocomplete_fields = ['work', 'cluster']
    filter_horizontal = ['spkr', 'addr']
    inlines = [SpeechTagInline]

    class Media:
        js = ['speechdb/admin_speech.js']

    @admin.display(description='Speakers')
    def get_speakers(self, obj):
        return ', '.join(s.name for s in obj.spkr.all())

    @admin.display(description='Addressees')
    def get_addressees(self, obj):
        return ', '.join(a.name for a in obj.addr.all())

@admin.register(SpeechCluster)
class SpeechClusterAdmin(BaseAdmin):
    readonly_fields = ["public_id"]
    list_display = ['public_id', 'get_loc', 'seq']
    search_fields = ['public_id']

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('speeches__work__author')

    @admin.display(description='Location')
    def get_loc(self, obj):
        return obj.get_loc_str() or '(empty)'

@admin.register(SpeechTag)
class SpeechTagAdmin(BaseAdmin):
    readonly_fields = ["public_id"]
    list_display = ['speech', 'type', 'doubt']
    list_filter = ['type', 'doubt']
    search_fields = ['speech__work__title']
    autocomplete_fields = ['speech']
