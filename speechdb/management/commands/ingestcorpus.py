from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from speechdb.models import Author, Work, Character, CharacterInstance, Speech, SpeechCluster
import csv
import os
import re
from django.core import serializers


def parseGender(gender):
    '''Try to match user-entered gender to allowable choices'''
    
    if gender is not None:
        gender = gender.upper().strip()
        if len(gender) > 0:
            gender = gender[0]
        else:
            gender = None
    
    if gender not in ['M', 'F', None]:
        gender = 'N'
    
    return gender


def parseBeing(being):
    '''Try to match user-entered "being" label to allowable choices'''
    
    if being is not None:
        being = being.lower().strip()
        if len(being) == 0:
            being = None
    
    if being not in ['human', 'god', None]:
        being = 'other'
    
    return being


def addAuthors(file):
    '''Parse the authors list from a TSV file'''
    f = open(file)
    reader = csv.DictReader(f, delimiter='\t')
        
    for rec in reader:
        a = Author()
        a.id = int(rec.get('id'))
        a.name = rec.get('name')
        a.wd = rec.get('wd')
        a.urn = rec.get('urn')
        a.save()


def addWorks(file):
    '''Parse the works list from a TSV file'''
    f = open(file)
    reader = csv.DictReader(f, delimiter='\t')
    
    for rec in reader:
        w = Work()
        w.id = int(rec.get('id'))
        auth_id = int(rec.get('author'))
        w.author = Author.objects.get(id=auth_id)
        w.title = rec.get('title')
        w.wd = rec.get('wd')
        w.urn = rec.get('urn')
        w.save()


def addChars(file):
    '''Parse the characters list from a TSV file'''
    f = open(file)
    reader = csv.DictReader(f, delimiter='\t')
    
    for rec in reader:
        c = Character()
        c.name = rec.get('name').strip() or None
        if c.name is None:
            print(f'Character {c.id} has no name. Skipping')
            continue
        if c.name == 'self':
            continue
        if len(Character.objects.filter(name=c.name)) > 0:
            print(f'Adding duplicate char name {c.name}.')
        c.wd = rec.get('wd').strip() or None
        if c.wd is None:
            print(f'{c} has no WikiData id.')
        being = rec.get('being').strip() or None
        if being is None:
            print(f'{c} has no being.')  
        else:
            c.being = being
        char_type = rec.get('type').strip() or None
        if char_type is None:
            print(f'{c} has no type.')
        else:
            c.type = char_type[0].upper()
        c.gender = parseGender(rec.get('gender'))
        c.notes = rec.get('notes').strip() or None
        c.save()

def addInst(name, speech):
    '''get or create character instance'''
    
    char_query_set = Character.objects.filter(name=name)
    if len(char_query_set) < 1:
        print(f'failed to find character {name}')
        return None
    if len(char_query_set) > 1:
        print(f'Multiple characters named {name}!')
    char = char_query_set.first()
    
    context = speech.cluster.work.title
    inst, created = CharacterInstance.objects.get_or_create(char=char, context=context)
    
    return inst


def addSpeeches(file):
    '''Parse the speeches list from a TSV file'''
    f = open(file)
    reader = csv.DictReader(f, delimiter='\t')
    
    for rec in reader:
        s = Speech()
        
        # text details
        s.seq = int(rec.get('seq'))
        book = rec.get('book').strip() or None
        if book is None:
            print(f'{s} has no book. skipping.')
            continue
        line_from = rec.get('from_line').strip() or None
        if line_from is None:
            print(f'{s} has no from_line. skipping.')
            continue
        line_to = rec.get('to_line').strip() or None
        if line_to is None:
            print(f'{s} has no to_line. skipping.')
            continue
        s.l_fi = f'{book}.{line_from}'
        s.l_la = f'{book}.{line_to}'
        
        # cluster details
        cluster_id = rec.get('cluster_id').strip() or None
        if cluster_id is None:
            print(f'{s} has no cluster ID: skipping.')
            continue
        try:
            s.cluster = SpeechCluster.objects.get(id=int(cluster_id))
        except SpeechCluster.DoesNotExist:
            c = SpeechCluster()
            c.id = cluster_id
            work_id = int(rec.get('work_id'))
            c.work = Work.objects.get(id=work_id)
            type_ = rec.get('simple_cluster_type').strip()[0].upper()
            if type_ in SpeechCluster.ClusterType.names:
                c.type = SpeechCluster.ClusterType[type_]
            elif type_ in SpeechCluster.ClusterType.values:
                c.type = type_
            else:
                print(f'Bad cluster type: {type_}')
            c.save()
            s.cluster = c

        part = rec.get('cluster_part').strip() or None
        if part is None:
            print(f'{s} has no part number.')
            part = 1
        s.part = int(part)
            
        s.save()
        
        # character details
        spkr_str = rec.get('speaker').strip() or None
        if spkr_str is None:
            print(f'{s} has no speakers: skipping.')
            s.delete()
            continue
        else:
            for name in spkr_str.split(' and '):
                inst = addInst(name, s)
                if inst is not None:
                    s.spkr.add(inst)
            if len(s.spkr.all()) < 1:
                print(f'{s} has no valid speakers. skipping.')
        s.spkr_notes = rec.get('speaker_notes').strip() or None
        
        addr_str = rec.get('addressee').strip() or None
        if addr_str is None:
            print(f'{s} has no addressees: skipping.')
            s.delete()
            continue
        else:
            for name in addr_str.split(' and '):
                if name == 'self':
                    inst = s.spkr.first()
                else:
                    inst = addInst(name, s)
                if inst is not None:
                    s.addr.add(inst)
            if len(s.addr.all()) < 1:
                print(f'{s} has no valid addressees. skipping.')
        s.addr_notes = rec.get('addressee_notes').strip() or None
        
        # other
        s.level = rec.get('embedded_level').strip() or None
        if s.level is not None:
            s.level = int(s.level)
        s.notes = rec.get('misc_notes').strip() or None
        
        s.save()


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
        addChars(char_file)

        # speeches, clusters, and char instances
        speech_files = [os.path.join(path, f) for f in sorted(os.listdir(path))
                        if f.startswith('speeches')]
        for speech_file in speech_files:
            self.stderr.write(f'Reading data from {speech_file}')
            addSpeeches(speech_file)