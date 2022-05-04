'''ingestcorpus - read full dataset from a directory of tsv files
'''


from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import django.db.utils
from speechdb.models import Metadata
from speechdb.models import Author, Work, Character, CharacterInstance, Speech, SpeechCluster, SpeechScene
import csv
import os
import re
import time
from django.core import serializers


def validate(s, choices, default=None, allow_none=False):
    '''Validate user input'''
    
    if s is not None:
        s = str(s).strip().lower()
        if len(s) == 0:
            s = None
    
    allowed = choices.values
    if allow_none:
        allowed.append(None)
    
    if s not in allowed:
        s = default.value
    
    return s


def addAuthors(file):
    '''Parse the authors list from a TSV file'''
    f = open(file)
    reader = csv.DictReader(f, delimiter='\t')
        
    for rec in reader:
        a = Author()
        a.id = int(rec.get('id').strip())
        a.name = rec.get('name').strip()
        a.wd = rec.get('wd').strip()
        a.urn = rec.get('urn').strip()
        a.save()


def addWorks(file):
    '''Parse the works list from a TSV file'''
    f = open(file)
    reader = csv.DictReader(f, delimiter='\t')
    
    for rec in reader:
        w = Work()
        w.id = int(rec.get('id').strip())
        auth_id = rec.get('author').strip()
        try:
            w.author = Author.objects.get(id=int(auth_id))
        except:
            print(f'Skipping work {w.id}: Can\'t parse author id "{auth_id}".')
            continue
        w.title = rec.get('title').strip()
        w.lang = rec.get('lang').strip()
        w.wd = rec.get('wd').strip()
        w.urn = rec.get('urn').strip()
        w.save()


def addChars(file):
    '''Parse the characters list from a TSV file'''
    f = open(file)
    reader = csv.DictReader(f, delimiter='\t')
    
    # a container for anonymous instances and alternate identities
    characters = {}
    alt_chars = {}
    anon_chars = {}
    
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
        c.manto = rec.get('manto').strip() or None
        c.anon = (rec.get('anon') is not None) and (
                    len(rec.get('anon').strip()) > 0)
        c.being = validate(rec.get('being'), Character.CharacterBeing,
                    default=Character.CharacterBeing.MORTAL)
        c.number = validate(rec.get('number'), Character.CharacterNumber,
                    default=Character.CharacterNumber.INDIVIDUAL)
        c.gender = validate(rec.get('gender'), Character.CharacterGender,
                    default=Character.CharacterGender.NA)
        c.same_as = rec.get('same_as').strip() or None
        c.notes = rec.get('notes').strip() or None
        
        c.tags = {}
        for col in rec.keys():
            if col.startswith('tag_'):
                key = col[4:]
                vals = []
                for tag in rec.get(col).split(','):
                    tag = tag.strip()
                    if tag != '':
                        vals.append(tag)
                if len(vals) > 0:
                    c.tags[key] = vals
        
        if c.being is None:
            print(f'Character {c} has no being')
        
        if c.name in characters or c.name in alt_chars or c.name in anon_chars:
            print(f'Multiple records for name {c.name}.')
        
        if c.same_as is not None:
            alt_chars[c.name] = c
        elif c.anon:
            anon_chars[c.name] = c
        else:
            characters[c.name] = c
            c.save()
            
    return characters, alt_chars, anon_chars

    
def addInst(name, speech, characters, alt_chars={}, anon_chars={}, 
            is_absent=False):
    '''get or create character instance'''
    
    # details of this instance
    instance_params = {
        'name': name,
        'context': speech.work.title,
    }

    # look for the name in characters list, alt ids, anonymous chars
    if name in characters:
        c = characters[name]
        instance_params['name'] = c.name
        instance_params['gender'] = c.gender
        instance_params['being'] = c.being
        instance_params['number'] = c.number
        instance_params['char'] = c
    elif name in alt_chars:
        c = alt_chars[name]
        instance_params['name'] = c.name
        instance_params['gender'] = c.gender
        instance_params['being'] = c.being
        instance_params['number'] = c.number
        try:
            instance_params['char'] = characters[c.same_as]
        except KeyError:
            print(f'Pseud {name} points to non-existent char {c.same_as}.')
            raise
    elif name in anon_chars:
        c = anon_chars[name]
        instance_params['name'] = c.name
        instance_params['gender'] = c.gender
        instance_params['being'] = c.being
        instance_params['number'] = c.number
        instance_params['anon'] = c.anon
        instance_params['tags'] = c.tags
    else:
        print(f'Failed to find character {name}.')
        return None
    
    instance_params['absent'] = is_absent
    
    #print(f'DEBUG: speech={speech}; params={instance_params}')
    inst, created = CharacterInstance.objects.get_or_create(**instance_params)
    
    return inst


def addSpeeches(file, characters, alt_chars={}, anon_chars={}):
    '''Parse the speeches list from a TSV file'''
    f = open(file)
    reader = csv.DictReader(f, delimiter='\t')
    
    skipped = []
    
    enclosed_and = re.compile(r'\[.+\sand\s.+\]')
    name_with_modifiers = re.compile(r'(\S.+?)\s*\[(.*)\]')
    
    seq = 0
    
    for rec in reader:
        s = Speech()
        errs = []
        
        # seq
        try:
            seq = int(rec.get('seq').strip())
            assert seq
        except ValueError:
            seq += 1
            errs.append('seq')
        s.seq = seq
        
        # id
        try:
            speech_id = int(rec.get('speech_id').strip())
        except ValueError:
            speech_id = None
            errs.append('speech_id')
            
        # alternate reading for an existing speech
        is_alt = bool(rec.get('alt').strip())
        
        if is_alt:
            # TODO: implement alternate records
            continue
            
        # edition
        edition = rec.get('edition').strip()

        # locus
        prefix_fi = rec.get('from_prefix').strip()
        if prefix_fi:
            prefix_fi += '.'
        else:
            prefix_fi = ''
            
        prefix_la = rec.get('to_prefix').strip()
        if prefix_la:
            prefix_la += '.'
        else:
            prefix_la = ''

        line_fi = rec.get('from_line').strip()
        if not line_fi:
            errs.append('from_line')

        line_la = rec.get('to_line').strip()
        if not line_la:
            errs.append('to_line')
    
        s.l_fi = prefix_fi + line_fi
        s.l_la = prefix_la + line_la
        
        
        # partial lines
        part_b = rec.get('b')
        if part_b is not None:
            part_b = part_b.strip().lower()
            if part_b.startswith('y') or part_b.startswith('b'):
                s.partial_b = True
        
        part_a = rec.get('a')
        if part_a is not None:
            part_a = part_a.strip().lower()
            if part_a.startswith('y') or part_a.startswith('a'):
                s.partial_a = True
        
        # work
        try:
            work_id = int(rec.get('work_id').strip())
        except ValueError:
            errs.append('work')
        s.work = Work.objects.get(id=work_id)

        # cluster type
        cluster_type = rec.get('simple_cluster_type').strip()
        if len(cluster_type) > 0:
            s.type = cluster_type[0].upper()
        else:
            errs.append('simple_cluster_type')
            # temp value: speech should be deleted
            s.type='M'

        # speech_scene
        try:
            scene_id = int(rec.get('speech_scene').strip())
        except ValueError:
            errs.append('scene_id')
            scene_id = 999999
            
        scene_title = rec.get('scene').strip()
        
        s.scene, created = SpeechScene.objects.get_or_create(id=scene_id)
        
        # speech cluster
        try:
            cluster_id = int(rec.get('cluster_id').strip())
        except ValueError:
            errs.append('cluster_id')
            # temp value: speech should be deleted            
            cluster_id = 999999
            
        s.cluster, created = SpeechCluster.objects.get_or_create(id=cluster_id)

        # cluster part
        try:
            part = int(rec.get('cluster_part').strip())
        except ValueError:
            errs.append('part')
            # temp value: speech should be deleted
            s.part = 1
        s.part = part

        # self-address
        s.self_addr = rec.get('inter se/secum').strip()
        
        # manual length
        s.manual_length = rec.get('length').strip()
        
        # frequency
        s.freq_notes = rec.get('frequency').strip()
        s.freq = bool(s.freq_notes)
            
        # misc notes
        s.notes = rec.get('misc_notes').strip()
        
        # speech must be saved before adding character instances
        s.save()
        
        # speakers
        spkr_str = rec.get('speaker').strip()
        if spkr_str:
        
            if enclosed_and.search(spkr_str):
                print('Found "and" within square brackets!')

            for name in spkr_str.split(' and '):
                if name_with_modifiers.search(name):
                    name = name_with_modifiers.sub(r'\1', name)
                inst = addInst(name, s, characters=characters, 
                        alt_chars=alt_chars, anon_chars=anon_chars)
                if inst is not None:
                    s.spkr.add(inst)
        if s.spkr.count() == 0:
            errs.append('speaker')
        
        # speaker notes
        s.spkr_notes = rec.get('speaker_notes').strip()

        # addressees        
        addr_str = rec.get('addressee').strip() 
        if addr_str:
            if enclosed_and.search(addr_str):
                print('Found "and" within square brackets!')
            
            addr = [name.strip() for name in addr_str.split(' and ')]
            
        else:
            addr = []
            print('No addressees!')
            
        # get the absent list
        absent_str = rec.get('absent_addressees').strip()
        if absent_str:
            absent = [name.strip() for name in absent_str.split(' and ')]
        else:
            absent = []

        # now check each addressee against absent

        for name in addr:
            if name == 'self':
                inst = s.spkr.first()
            else:
                if name_with_modifiers.search(name):
                    name = name_with_modifiers.sub(r'\1', name)
                
                inst = addInst(name, s, characters=characters,
                        alt_chars=alt_chars, anon_chars=anon_chars, 
                        is_absent=(name in absent))
            s.addr.add(inst)

        # addressee notes
        s.addr_notes = rec.get('addressee_notes').strip()
        
        # manually entered number of addressees
        addr_num = rec.get('addressee_number').strip()
        if addr_num == '∞':
            s.addr_num = Speech.CharacterNumber.MANY
        elif int(addr_num) == 1:
            s.addr_num = Speech.CharacterNumber.ONE
        elif int(addr_num) > 1:
            s.addr_num = Speech.CharacterNumber.MANY
        else:
            errs.append('addressee_number')

        # manually entered number of absent addressees
        absent_num = rec.get('absent_number')
        if absent_num:
            if absent_num == '∞':
                s.absent_num = Speech.CharacterNumber.MANY
            elif int(absent_num) == 1:
                s.absent_num = Speech.CharacterNumber.ONE
            elif int(absent_num) > 1:
                s.absent_num = Speech.CharacterNumber.MANY
            else:
                errs.append('absent_number')
        else:
            absent_num = Speech.CharacterNumber.ZERO
            
        # bystanders
        byst_str = rec.get('bystanders').strip()
        if byst_str.lower() == 'unspecified':
            s.bystanders_num = Speech.CharacterNumber.UNSPECIFIED
        elif byst_str.lower() == 'none':
            s.bystanders_num = Speech.CharacterNumber.ZERO
        elif byst_str != '':
            for name in byst_str.split(' and '):
                inst = addInst(name, s, characters=characters,
                        alt_chars=alt_chars, anon_chars=anon_chars)
                if inst is not None:
                    s.bystanders.add(inst)
            if s.bystanders.count() == 1:
                s.bystanders_num = Speech.CharacterNumber.ONE
            elif s.bystanders.count() > 1:
                s.bystanders_num = Speech.CharacterNumber.MANY
        else:
            errs.append('bystanders_num')
        
        # embeddedness
        try:
            level = int(rec.get('embedded_level').strip())
        except ValueError:
            errs.append('invalid_embedded_level')
            
            if s.cluster.embedded_level is None:
                s.cluster.embedded_level = level
            else:
                if s.cluster.embedded_level != level:
                    errs.append('embedded_level_mismatch')
        
        # general notes
        s.notes = rec.get('misc_notes').strip() or None
        
        # save speech or log errors
        if len(errs) == 0:
            s.save()
        else:
            skipped.append((reader.line_num, str(s), errs))
            s.delete()
    
    if len(skipped) > 0:
        print(f'skipped {len(skipped)} rows:')
        for line_num, speech, errs in skipped:
            print(line_num, speech, errs)


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
        characters, alt_chars, anon_chars = addChars(char_file)

        # speeches, clusters, and char instances
        speech_files = [os.path.join(path, f) for f in sorted(os.listdir(path))
                        if f.startswith('speeches')]
        for speech_file in speech_files:
            self.stderr.write(f'Reading data from {speech_file}')
            addSpeeches(speech_file, characters=characters, alt_chars=alt_chars,
                        anon_chars=anon_chars)
        
        # metadata
        Metadata(name='version', value='0.1').save()
        Metadata(name='date', value=time.strftime('%Y-%m-%d %H:%M:%S %z')).save()