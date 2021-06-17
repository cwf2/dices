from django.db import models

# Entity classes

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
    
    class CharacterNumber(models.TextChoices):
        INDIVIDUAL = ('individual', 'Individual')
        COLLECTIVE = ('collective', 'Collective')
        OTHER = ('other', 'Other')

    class CharacterBeing(models.TextChoices):
        MORTAL = ('mortal', 'Mortal')
        DIVINE = ('divine', 'Divine')
        CREATURE = ('creature', 'Mythical Creature')
        OTHER = ('other', 'Other')
        
    class CharacterGender(models.TextChoices):
        NB = ('non-binary', 'Non-binary')
        FEMALE = ('female', 'Female')
        MALE = ('male', 'Male')
    
    name = models.CharField(max_length=64)
    being = models.CharField(max_length=16, choices=CharacterBeing.choices,
            default=CharacterBeing.MORTAL)
    number = models.CharField(max_length=16, choices=CharacterNumber.choices,
            default=CharacterNumber.INDIVIDUAL)
    gender = models.CharField(max_length=16, null=True, blank=True,
            choices=CharacterGender.choices)
    wd = models.CharField('WikiData ID', max_length=32, null=True)
    manto = models.CharField('MANTO ID', max_length=32, null=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class CharacterInstance(models.Model):
    '''A character engaged in a speech'''
    
    name = models.CharField(max_length=64, null=True, blank=True)
    being = models.CharField(max_length=16, null=True, blank=True,
            choices=Character.CharacterBeing.choices)
    number = models.CharField(max_length=16, null=True, blank=True,
            choices=Character.CharacterNumber.choices)
    gender = models.CharField(max_length=16, null=True, blank=True,
            choices=Character.CharacterGender.choices)
    char = models.ForeignKey(Character, related_name='instances', 
            blank=True, null=True, on_delete=models.PROTECT)
    disg = models.ForeignKey(Character, related_name='disguises', 
            blank=True, null=True, on_delete=models.PROTECT)
    anon = models.BooleanField(default=False)
    #TODO tuple (char, context) should be unique
    context = models.CharField(max_length=128)
    tags = models.JSONField(default=dict)
    
    class Meta:
        ordering = ['char']
    
    def __str__(self):
        return self.get_long_name()

    def get_name(self):
        '''returns top-level name'''
        if self.disg is not None:
            name = self.disg.name
        elif self.name is not None:
            name = self.name
        else:
            name = self.char.name
            
        return name

    def get_gender(self):
        '''returns top-level gender'''
        if self.disg is not None:
            char_gender = self.disg.gender
        else:
            char_gender = self.char.gender
        
        return self.gender or char_gender

    def get_being(self):
        '''returns top-level being'''
        if self.disg is not None:
            char_being = self.disg.being
        else:
            char_being = self.char.being
        
        return self.being or char_being

    def get_number(self):
        '''returns top-level being'''
        if self.disg is not None:
            char_number = self.disg.number
        else:
            char_number = self.char.number
        
        return self.number or char_number
    
    def get_long_name(self):
        '''returns char name, including instance name and/or disguise'''
        name = self.get_name()
        
        if name != self.char.name:
            name += '/' + self.char.name
        
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
        ordering = ['cluster__work__id', 'seq']
    
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