from django.db import models

class Author(models.Model):
    '''An ancient author'''
    
    name = models.CharField(max_length=64)
    wd = models.CharField('WikiData ID', max_length=32)
    urn = models.CharField(max_length=64)
    
    def __str__(self):
        return self.name


class Work(models.Model):
    '''An epic text'''
    
    title = models.CharField(max_length=64)
    wd = models.CharField('WikiData ID', max_length=32)
    urn = models.CharField(max_length=128)
    author = models.ForeignKey(Author, on_delete=models.PROTECT)
    
    def __str__(self):
        return f'{self.author.name} {self.title}'
    
    def get_long_name(self):
        '''Return common name as a string'''
        return f'{self.author.name} {self.title}'


class Character(models.Model):
    '''An epic character'''
    character_type_choices = [
        ('I', 'individual'),
        ('C', 'collective'),
        ('O', 'other'),
    ]
    character_type_lookup = dict(character_type_choices)
    
    name = models.CharField(max_length=64)
    being = models.CharField(max_length=16, default='human')
    type = models.CharField(max_length=1, choices=character_type_choices,
            default='I', blank=False)
    wd = models.CharField('WikiData ID', max_length=32, unique=True)
    manto = models.CharField('MANTO ID', max_length=32, blank=True)

    def __str__(self):
        return self.name

    def get_long_type(self):
        return Character.character_type_lookup[self.type]

class CharacterInstance(models.Model):
    '''A character engaged in a speech'''
    
    char = models.ForeignKey(Character, related_name='instances', 
            on_delete=models.PROTECT)
    disg = models.ForeignKey(Character, related_name='disguises', 
            blank=True, null=True, on_delete=models.PROTECT)
    #TODO tuple (char, context) should be unique
    context = models.CharField(max_length=128)
    
    def __str__(self):
        name = self.char.name
        if self.disg is not None:
            name += '/' + self.disg.name
        return name


class SpeechCluster(models.Model):
    '''A group of related speeches'''
    
    speech_type_choices = [
        ('S', 'Soliloqy'),
        ('M', 'Monologue'),
        ('D', 'Dialogue'),
        ('G', 'General'),
    ]
    speech_type_lookup = dict(speech_type_choices)
    
    type = models.CharField(max_length=1, choices=speech_type_choices)
    work = models.ForeignKey(Work, on_delete=models.PROTECT)
    
    # def __str__(self):
    #     if self.speech_set is not None:
    #         loc = '{w} {l}'.format(
    #             w = self.work,
    #             l = self.speech_set.order_by('part')[0].l_fi,
    #         )
    #         n = len(self.speech_set.all())
    #         if n > 1:
    #             parts = f'{n} parts'
    #         else:
    #             parts = '1 part'
    #     else:
    #         parts = 'empty'
    #     return f'{loc} {self.type} [{parts}]'
    
    def get_spkr_str(self):
        '''Return speaker list as a string'''
        chars = []
        for speech in self.speech_set.all():
            chars.extend([str(c) for c in speech.spkr.all()])
        chars = sorted(set(chars))
        return ', '.join(chars)
    
    def get_addr_str(self):
        '''Return addressee list as a string'''
        chars = []
        for speech in self.speech_set.all():
            chars.extend([str(c) for c in speech.addr.all()])
        chars = sorted(set(chars))
        return ', '.join(chars)
        
    def get_chars_str(self):
        chars = []
        for speech in self.speech_set.all():
            chars.extend([str(c) for c in speech.spkr.all()])
            chars.extend([str(c) for c in speech.addr.all()])
        chars = sorted(set(chars))
        return ', '.join(chars)
        
    def get_long_type(self):
        return SpeechCluster.speech_type_lookup[self.type]

class Speech(models.Model):
    '''A direct speech instance'''
    
    cluster = models.ForeignKey(SpeechCluster, on_delete=models.CASCADE)
    seq = models.IntegerField()
    l_fi = models.CharField('first line', max_length=8)
    l_la = models.CharField('last line', max_length=8)
    spkr = models.ManyToManyField(CharacterInstance, related_name='speeches')
    addr = models.ManyToManyField(CharacterInstance, related_name='addresses',
             blank=True)
    # TODO should be unique per cluster
    part = models.IntegerField()
    
    def __str__(self):
        return f'{self.cluster.work} {self.l_fi}-{self.l_la}'
        
    def get_urn(self):
        '''Return CTS URN for the whole speech'''
        return f'{self.cluster.work.urn}:{self.l_fi}-{self.l_la}'
        
    def get_spkr_str(self):
        '''Return speaker list as a string'''
        return ', '.join([str(s) for s in self.spkr.all()])
    
    def get_addr_str(self):
        '''Return speaker list as a string'''
        return ', '.join([str(s) for s in self.addr.all()])
        
    def get_short_type(self):
        '''Return one-char type designation'''
        t = self.cluster.type
        if t == 'D':
            t += str(self.part)
        return t