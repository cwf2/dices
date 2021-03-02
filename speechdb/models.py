from django.db import models

class Author(models.Model):
    '''An ancient author'''
    
    name = models.CharField(max_length=64)
    wd = models.CharField('WikiData ID', max_length=32)
    urn = models.CharField(max_length=64)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Work(models.Model):
    '''An epic text'''
    
    title = models.CharField(max_length=64)
    wd = models.CharField('WikiData ID', max_length=32)
    urn = models.CharField(max_length=128)
    author = models.ForeignKey(Author, on_delete=models.PROTECT)
    
    class Meta:
        ordering = ['author', 'title']
    
    def __str__(self):
        return f'{self.author.name} {self.title}'
    
    def get_long_name(self):
        '''Return common name as a string'''
        return f'{self.author.name} {self.title}'


class Character(models.Model):
    '''An epic character'''
    INDIVIDUAL = 'I'
    COLLECTIVE = 'C'
    OTHER = 'O'
    
    character_type_choices = [
        (INDIVIDUAL, 'individual'),
        (COLLECTIVE, 'collective'),
        (OTHER, 'other'),
    ]
    
    name = models.CharField(max_length=64)
    being = models.CharField(max_length=32, default='human')
    type = models.CharField(max_length=1, choices=character_type_choices,
            default='I')
    wd = models.CharField('WikiData ID', max_length=32, null=True)
    manto = models.CharField('MANTO ID', max_length=32, null=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class CharacterInstance(models.Model):
    '''A character engaged in a speech'''
    
    char = models.ForeignKey(Character, related_name='instances', 
            on_delete=models.PROTECT)
    disg = models.ForeignKey(Character, related_name='disguises', 
            blank=True, null=True, on_delete=models.PROTECT)
    #TODO tuple (char, context) should be unique
    context = models.CharField(max_length=128)
    
    class Meta:
        ordering = ['char']
    
    def __str__(self):
        return self.get_long_name()
    
    def get_long_name(self):
        name = self.char.name
        if self.disg is not None:
            name += '/' + self.disg.name
        return name


class SpeechCluster(models.Model):
    '''A group of related speeches'''
    
    class ClusterType(models.TextChoices):
        SOLILOQUY = ('S', 'Soliloquy')
        MONOLOGUE = ('M', 'Monologue')
        DIALOGUE = ('D', 'Dialogue')
        GENERAL = ('G', 'General')
        
    type = models.CharField(max_length=1, choices=ClusterType.choices)
    work = models.ForeignKey(Work, on_delete=models.PROTECT)
    
    class Meta:
        ordering = ['work', 'speech']
    
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
    
    class Meta:
        ordering = ['cluster__work', 'seq']
    
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