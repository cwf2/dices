from django.db import models

# Metadata about the database itself
class Metadata(models.Model):
    name = models.CharField(max_length=64, blank=False, unique=True)
    value = models.TextField()

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

    class Language(models.TextChoices):
        GREEK = ('greek', 'Greek')
        LATIN = ('latin', 'Latin')
    
    title = models.CharField(max_length=64)
    wd = models.CharField('WikiData ID', max_length=32)
    urn = models.CharField(max_length=128)
    author = models.ForeignKey(Author, on_delete=models.PROTECT)
    lang = models.CharField(max_length=8, choices=Language.choices)
    
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
        NA = ('none', 'Unknown/not-applicable')
        NB = ('non-binary', 'Mixed/non-binary')
        FEMALE = ('female', 'Female')
        MALE = ('male', 'Male')

    
    name = models.CharField(max_length=64)
    being = models.CharField(max_length=16, choices=CharacterBeing.choices,
            default=CharacterBeing.MORTAL)
    number = models.CharField(max_length=16, choices=CharacterNumber.choices,
            default=CharacterNumber.INDIVIDUAL)
    gender = models.CharField(max_length=16, choices=CharacterGender.choices,
            default=CharacterGender.NA)
    wd = models.CharField('WikiData ID', max_length=32, null=True)
    manto = models.CharField('MANTO ID', max_length=32, null=True)


    class Meta:
        ordering = ['name']


    def __str__(self):
        return self.name


class CharacterInstance(models.Model):
    '''A character engaged in a speech'''
    
    name = models.CharField(max_length=64)
    being = models.CharField(max_length=16, 
            choices=Character.CharacterBeing.choices,
            default=Character.CharacterBeing.MORTAL)
    number = models.CharField(max_length=16,
            choices=Character.CharacterNumber.choices,
            default=Character.CharacterNumber.INDIVIDUAL)
    gender = models.CharField(max_length=16,
            choices=Character.CharacterGender.choices,
            default=Character.CharacterGender.NA)
    char = models.ForeignKey(Character, related_name='instances', 
            blank=True, null=True, on_delete=models.PROTECT)
    disg = models.ForeignKey(Character, related_name='disguises', 
            blank=True, null=True, on_delete=models.PROTECT)
    anon = models.BooleanField(default=False)
    possessed = models.ForeignKey(Character, related_name='possessions',
            blank=True, null=True, on_delete=models.PROTECT)
    dead = models.BooleanField(default=False)
    absent = models.BooleanField(default=False)
    absent_notes = models.CharField(max_length=128, blank=True)
    #TODO tuple (char, context) should be unique
    context = models.CharField(max_length=128)
    tags = models.JSONField(default=dict)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.get_long_name()
    
    def get_long_name(self):
        '''returns char name, including instance name and/or disguise'''
        name = self.name
        
        if self.char is not None:
            if name != self.char.name:
                name += '/' + self.char.name
        
        return name


class SpeechScene(models.Model):
    '''A group of speech clusters sharing location/characters'''
    
    title = models.CharField(max_length=64)
    

class SpeechCluster(models.Model):
    '''A group of related speeches'''

    class Meta:
        ordering = ['speech']

    class ClusterType(models.TextChoices):
        SOLILOQUY = ('S', 'Soliloquy')
        MONOLOGUE = ('M', 'Monologue')
        DIALOGUE = ('D', 'Dialogue')
        GENERAL = ('G', 'General')

    # embeddedness
    embedded_in = models.ForeignKey('Speech', on_delete=models.CASCADE, null=True)
    embedded_level = models.IntegerField(null=True)
    
    # type
    type = models.CharField(max_length=1, choices=ClusterType.choices)
                
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

    @property
    def speakers(self):
        speakersSquares = [speech.spkr.all() for speech in self.speech_set.all()]
        newlist = []
        for speakerChunk in speakersSquares:
            for speaker in speakerChunk:
                newlist.append(speaker)
        return set(newlist)
    
    @property
    def addressees(self):
        addressesSquares = [speech.addr.all() for speech in self.speech_set.all()]
        newlist = []
        for addresseeChunk in addressesSquares:
            for addressee in addresseeChunk: 
                newlist.append(addressee)
        return set(newlist)
        
        

class Speech(models.Model):
    '''A direct speech instance'''
    
    class CharacterNumber(models.TextChoices):
        UNSPECIFIED = ('', 'Unspecified')        
        ZERO = ('0', 'None')
        ONE = ('1', 'Single')
        MANY = ('∞', 'Group')
        
    seq = models.IntegerField()

    # cluster and part within cluster
    cluster = models.ForeignKey(SpeechCluster, on_delete=models.CASCADE)
    part = models.IntegerField()

    # loci of first and last lines
    work = models.ForeignKey('Work', on_delete=models.CASCADE)
    l_fi = models.CharField('first line', max_length=8)
    l_la = models.CharField('last line', max_length=8)
    
    # begins mid-line
    partial_b = models.BooleanField(default=False)
    # ends mid-line
    partial_a = models.BooleanField(default=False)
    
    # speakers
    spkr = models.ManyToManyField(CharacterInstance, related_name='speeches')
    spkr_num = models.CharField(max_length=1, choices=CharacterNumber.choices,
        blank=True)
    
    # addressees
    addr = models.ManyToManyField(CharacterInstance, related_name='addresses',
             blank=True)
    addr_num = models.CharField(max_length=1, choices=CharacterNumber.choices,
        blank=True)
    absent_num = models.CharField(max_length=1, choices=CharacterNumber.choices,
        blank=True)
        
    # witnesses to speech
    bystanders = models.ManyToManyField(CharacterInstance, 
        related_name='addresses_as_bystander', blank=True)
    bystanders_num = models.CharField(max_length=1, choices=CharacterNumber.choices,
        blank=True)
    
    # phrase used for self address (inter se / secum)
    self_addr = models.CharField(max_length=16, blank=True)
    
    # is the speech repeated or frequentative
    freq = models.BooleanField(default=False)
    freq_notes = models.CharField(max_length=128, blank=True)
    
    # manually-recorded length
    manual_length = models.CharField(max_length=16, blank=True)
    
    # general notes for the speech
    notes = models.TextField(blank=True, null=True)
    
    
    class Meta:
        ordering = ['work', 'seq']
    
    def __str__(self):
        return f'{self.work} {self.l_fi}-{self.l_la}'
        
    def get_urn(self):
        '''Return CTS URN for the whole speech'''
        return f'{self.work.urn}:{self.l_fi}-{self.l_la}'
        
    def get_spkr_str(self):
        '''Return speaker list as a string'''
        return ', '.join([str(s) for s in self.spkr.all()])
    
    def get_addr_str(self):
        '''Return speaker list as a string'''
        return ', '.join([str(s) for s in self.addr.all()])
        
    def get_short_type(self):
        '''Return one-char type designation'''
        t = self.cluster.type
        if t == 'D' or t == 'G':
            t += str(self.part)
        return t