from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import django.db.utils
from speechdb.models import Metadata, IntegrityError
from speechdb.models import Author, Work, Character, CharacterInstance
from speechdb.models import Speech, SpeechCluster, SpeechTag
import csv
import os
import re
import time
from django.core import serializers
from git import Repo


def validate(s, choices=None, allow_na=False, na_value="", transform=None):
    '''Validate user input'''
    
    # strip whitespace
    s = s or ""
    s = str(s).strip()
    
    if transform:
        s = transform(s)
    
    # if choices, make sure s is one of them
    if choices is not None:
        for val in list(choices.values):
            if s.lower() == val.lower():
                s = val
                break
        if s not in choices.values:
            raise ValueError(f"Can't validate field value {s}")

    # if na, see whether allowed
    if s == "":
        if allow_na:
            return na_value
        else:
            raise ValueError("Can't validate null value")
    else:
        return s


def addAuthors(file):
    '''Parse the authors list from a TSV file'''
    
    with open(file) as f:
        reader = csv.DictReader(f, delimiter='\t')
        
        for rec in reader:
            a = Author()
            a.id = int(rec.get('id').strip())
            try:
                a.name = validate(rec.get('name'))
            except:
                print(rec)
                raise
            a.wd = validate(rec.get('wd'), allow_na=True)
            a.urn = validate(rec.get('urn'), allow_na=True)
            a.save()


def addWorks(file):
    '''Parse the works list from a TSV file'''

    with open(file) as f:
        reader = csv.DictReader(f, delimiter='\t')
    
        for rec in reader:
            w = Work()
            w.id = int(validate(rec.get('id')))
            auth_id = int(validate(rec.get('author')))
            try:
                w.author = Author.objects.get(id=auth_id)
            except:
                raise ValueError(f'Failed on work {w}: Can\'t parse author id "{auth_id}".')

            w.title = validate(rec.get('title'))
            w.lang = validate(rec.get('lang'), choices=Work.Language)
            w.wd = validate(rec.get('wd'), allow_na=True)
            w.urn = validate(rec.get('urn'), allow_na=True)
            w.tlg = validate(rec.get('tlg'), allow_na=True)
            w.save()



def addCharacters(file):
    '''Parse the characters list from a TSV file
    
        NEW VERSION!
    '''

    with open(file) as f:
        reader = csv.DictReader(f, delimiter='\t')
    
        for rec in reader:
            c = Character()
        
            # name
            c.name = validate(rec.get('name'))
        
            # being
            c.being = validate(rec.get('being'), Character.CharacterBeing)

            # number
            c.number = validate(rec.get('number'), Character.CharacterNumber)

            # gender
            c.gender = validate(rec.get('gender'), Character.CharacterGender)

            # wikidata id
            c.wd = validate(rec.get('wd'), allow_na=True)
            
            # manto id
            c.manto = validate(rec.get('manto'), allow_na=True)
            
            # topostext id
            c.tt = validate(rec.get('topostext'), allow_na=True)
            
            # notes
            c.notes = validate(rec.get('notes'), allow_na=True)
        
            c.save()



def getInstances(file):
    '''Parse the character instances list from a TSV file
    
        because instance contexts are generated from speech records,
        we can't populate CharacterInstances yet. Instead, we return
        a dictionary indexing instance attributes by name.
    '''
    
    with open(file) as f:
        reader = csv.DictReader(f, delimiter='\t')
        
        instances = {}
        
        for rec in reader:
            inst = dict(
                name = validate(rec.get('name')),
                being = validate(rec.get('being'), Character.CharacterBeing),
                number = validate(rec.get('number'), Character.CharacterNumber),
                gender = validate(rec.get('gender'), Character.CharacterGender),
                disguise = validate(rec.get('disguise'), allow_na=True),
                char = None,
                anon = validate(rec.get('anon'), allow_na=True) == 'yes',
                notes = validate(rec.get('notes'), allow_na=True),
            )
            
            # display name defaults to instance name
            inst["display"] = validate(rec.get('screen name'), allow_na=True) or inst["name"]
            
            # if instance of, check character list
            char_name = validate(rec.get('instance of'), allow_na=True)
            if char_name:
                qs = Character.objects.filter(name=char_name)
                if len(qs) < 1:
                    raise ValueError(f"Instance failed on character name: {rec}")
                elif len(qs) > 1:
                    raise IntegrityError(f"Instance matches two character names: {rec}")
                else:
                    inst["char"] = qs.first()
                    
            # otherwise, check instance name against character list
            else:
                qs = Character.objects.filter(name=inst["name"])
                if len(qs) > 1:
                    raise IntegrityError(f"Instance matches two character names: {rec}")
                elif len(qs) == 1:
                    inst["char"] = qs.first()
            
            instances[inst["name"]] = inst
            
    return instances
            

def addSpeeches(file, instances):
    '''Parse the speeches list from a TSV file'''
    
    with open(file) as f:
        reader = csv.DictReader(f, delimiter='\t')
    
        for rec in reader:
            try:
                s = Speech()
        
                # sequence
                s.seq = int(validate(rec.get('seq')))
        
                # locus
                book_fi = validate(rec.get('from_book'), allow_na=True)
                if book_fi:
                    book_fi += '.'
                else:
                    book_fi = ''
            
                book_la = validate(rec.get('to_book'), allow_na=True)
                if book_la:
                    book_la += '.'
                else:
                    book_la = ''

                line_fi = validate(rec.get('from_line'))
                line_la = validate(rec.get('to_line'))
    
                s.l_fi = book_fi + line_fi
                s.l_la = book_la + line_la
        
                # work
                work_id = int(validate(rec.get('work_id')))
                s.work = Work.objects.get(id=work_id)            

                # cluster type
                s.type = validate(rec.get('turn_type'), choices=Speech.SpeechType, transform=lambda s: s[0])
        
                # cluster_id
                cluster_id = int(validate(rec.get('cluster_id')))
                s.cluster, cluster_created = SpeechCluster.objects.get_or_create(id=cluster_id)

                # cluster part
                s.part = int(validate(rec.get('cluster_part')))
            
                # embeddedness
                s.level = int(validate(rec.get('embedded_level')))
        
                # speaker notes
                s.spkr_notes = validate(rec.get('speaker_notes'), allow_na=True)
        
                # addressee notes
                s.addr_notes = validate(rec.get('addressee_notes'), allow_na=True)
        
                # general notes
                s.notes = validate(rec.get('misc_notes'), allow_na=True)

                # speech must be saved before adding character instances
                s.save()

            except:
                print(s)
                raise
                    
            # generate context from work
            context = s.work.get_long_name()
                    
            # speakers
            spkr_str = validate(rec.get('speaker'))

            for name in spkr_str.split(';'):
                if name in instances:
                    inst, inst_created = CharacterInstance.objects.get_or_create(
                        name = name,
                        display = instances[name]["display"],
                        context = context,
                        being = instances[name]["being"],
                        number = instances[name]["number"],
                        gender = instances[name]["gender"],
                        disguise = instances[name]["disguise"],
                        char = instances[name]["char"],
                        anon = instances[name]["anon"],
                        notes = instances[name]["notes"],
                    )
                    s.spkr.add(inst)
                else:
                    raise ValueError(f"speech {s} failed on speaker {name}")
            assert len(s.spkr.all()) > 0
            
            # addressees            
            addr_str = validate(rec.get('addressee'))

            for name in addr_str.split(';'):
                if name == 'self':
                    inst = s.spkr.first()
                else: 
                    if name in instances:
                        inst, inst_created = CharacterInstance.objects.get_or_create(
                            name = name,
                            display = instances[name]["display"],
                            context = context,
                            being = instances[name]["being"],
                            number = instances[name]["number"],
                            gender = instances[name]["gender"],
                            disguise = instances[name]["disguise"],
                            char = instances[name]["char"],
                            anon = instances[name]["anon"],
                            notes = instances[name]["notes"],
                        )
                    else:
                        raise ValueError(f"speech {s} failed on addressee {name}")
                s.addr.add(inst)
            assert len(s.addr.all()) > 0
            
            s.save()
            
            # speech type tags
            tag_str = validate(rec.get('short_speech_type'), allow_na=True)
            for tag in tag_str.split(';'):
                tag = tag.strip().lower()
                doubt = tag.endswith('?')
                tag = tag.strip(' ?')
                if tag is not None and len(tag) > 0:
                    if tag not in SpeechTag.TagType.values:
                        raise ValueError(f"speech {s} failed on undefined tag {tag}")
                    t = SpeechTag(type=tag, speech=s, doubt=doubt)
                    t.save()
            

class Command(BaseCommand):
    help = 'Check data integrity?'
    
    def add_arguments(self, parser):
        parser.add_argument('path', type=str)
    
    def handle(self, *args, **options):
        path = options['path']

        # authors
        auth_file = os.path.join(path, 'authors')
        self.stderr.write(f'Reading data from {auth_file}')
        addAuthors(auth_file)

        # works
        work_file = os.path.join(path, 'works')
        self.stderr.write(f'Reading data from {work_file}')
        addWorks(work_file)

        # characters
        char_file = os.path.join(path, 'characters')
        self.stderr.write(f'Reading data from {char_file}')
        addCharacters(char_file)

        # instances
        inst_file = os.path.join(path, 'instances')
        self.stderr.write(f'Reading data from {inst_file}')
        instances = getInstances(inst_file)

        # speeches, clusters, and char instances
        speech_files = [os.path.join(path, f) for f in sorted(os.listdir(path))
                        if f.startswith('speeches')]
        for speech_file in speech_files:
            self.stderr.write(f'Reading data from {speech_file}')
            addSpeeches(speech_file, instances=instances)
                        
        # set sort-order for speech clusters
        cluster_index = {}
        sort_key = 0
        for speech in Speech.objects.all():
            cluster_id = speech.cluster.pk
            if cluster_id not in cluster_index:
                cluster_index[cluster_id] = sort_key
                sort_key += 1
        for cluster in SpeechCluster.objects.all():
            cluster.seq = cluster_index[cluster.pk]
            cluster.save()
        
        # get current git hash
        repo = Repo(search_parent_directories=True)
        if repo:
            commit_hash = repo.head.object.hexsha
        else:
            commit_hash = ""
        
        # metadata
        Metadata(name='version', value='1.1').save()
        Metadata(name='date', value=time.strftime('%Y-%m-%d %H:%M:%S %z')).save()
        Metadata(name='git-commit', value=commit_hash).save()