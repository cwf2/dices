from django.db import models, IntegrityError
from django.utils.functional import cached_property
import secrets

URN_BASE = "https://db.dices.mta.ca/app"

class PublicIdModel(models.Model):
    '''a base class that incorporates a public-facing unique id in all records
        - every new record gets a `public_id` field, a four-digit hex code
        - this is suitable for generating record-specific URNs
    '''

    # expect four character string
    public_id = models.CharField(max_length=4, unique=True, editable=False)
        
    class Meta:
         abstract = True
    
    @property
    def dices_urn(self):
        '''return a urn for the object using project namespace'''
        
        return f"{URN_BASE}/{self.__class__.__name__}/{self.public_id}"
    
    
    # overload the save method to generate a unique public_id value
    def save(self, *args, **kwargs):
        if not self.public_id:
            for _ in range(100):
                
                # generate four-digit hex
                candidate = f"{secrets.randbits(16):04X}"
                if not type(self).objects.filter(public_id=candidate).exists():
                    self.public_id = candidate
                    break
            else:
                raise IntegrityError("No available unique public_id after 100 attempts")
        super().save(*args, **kwargs)

# Metadata about the database itself
class Metadata(PublicIdModel):
    name = models.CharField(max_length=128, blank=False, unique=True)
    value = models.TextField()

# Entity classes

class Author(PublicIdModel):
    '''An ancient author'''
    
    name = models.CharField(max_length=128)
    wd = models.CharField('WikiData ID', max_length=32, blank=True, default="")
    urn = models.CharField(max_length=128, blank=True, default="")
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Work(PublicIdModel):
    '''An epic text'''

    class Language(models.TextChoices):
        GREEK = ('greek', 'Greek')
        LATIN = ('latin', 'Latin')
        
    title = models.CharField(max_length=128)
    wd = models.CharField('WikiData ID', max_length=32, blank=True, default="")
    tlg = models.CharField(max_length=12, blank=True, default="")
    urn = models.CharField(max_length=128, blank=True, default="")
    author = models.ForeignKey(Author, on_delete=models.PROTECT)
    lang = models.CharField(max_length=8, choices=Language.choices)
    
    class Meta:
        ordering = ['author', 'title']


    def __str__(self):
        return self.get_long_name()

    
    def get_long_name(self):
        '''Return common name as a string'''
        if self.author.name == "Anonymous":
            return self.title
        else:
            return f'{self.author.name}, {self.title}'


class Character(PublicIdModel):
    '''An epic character'''
    
    class CharacterNumber(models.TextChoices):
        INDIVIDUAL = ('individual', 'Individual')
        COLLECTIVE = ('collective', 'Collective')


    class CharacterBeing(models.TextChoices):
        MORTAL = ('mortal', 'Mortal')
        DIVINE = ('divine', 'Divine')
        CREATURE = ('creature', 'Mythical Creature')
        OTHER = ('other', 'Other')
        

    class CharacterGender(models.TextChoices):
        MALE = ('male', 'Male')
        FEMALE = ('female', 'Female')
        NB = ('x', 'Mixed/non-binary')
        NA = ('none', 'Unknown/not-applicable')

    name = models.CharField(max_length=128)
    being = models.CharField(max_length=16, choices=CharacterBeing.choices,
            default=CharacterBeing.MORTAL)
    number = models.CharField(max_length=16, choices=CharacterNumber.choices,
            default=CharacterNumber.INDIVIDUAL)
    gender = models.CharField(max_length=16, choices=CharacterGender.choices,
            default=CharacterGender.NA)
    wd = models.CharField('WikiData ID', max_length=32, blank=True, default="")
    manto = models.CharField('MANTO ID', max_length=32, blank=True, default="")
    tt = models.CharField('ToposText ID', max_length=32, blank=True, default="")
    notes = models.CharField('Notes', max_length=256, blank=True, default="")

    class Meta:
        ordering = ['name']


    def __str__(self):
        return self.name
        
    def get_speeches(self):
        return Speech.objects.filter(spkr__char__id=self.id)

    def get_addresses(self):
        return Speech.objects.filter(addr__char__id=self.id)


class CharacterInstance(PublicIdModel):
    '''A character engaged in a speech'''

    name = models.CharField(max_length=128)
    display = models.CharField(max_length=128)
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
            null=True, on_delete=models.PROTECT)
    disguise = models.CharField(max_length=128, blank=True, default="")
    anon = models.BooleanField(default=False)
    notes = models.CharField(max_length=256, blank=True, default="")
    context = models.CharField(max_length=128)
    
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
    
    def get_speeches(self):
        '''returns set of speeches by all instances of underlying char'''
        return Speech.objects.filter(spkr__char=self.char)
    
    def get_addresses(self):
        '''returns set of speeches by all instances of underlying char'''
        return Speech.objects.filter(addr__char=self.char)


class SpeechCluster(PublicIdModel):
    '''A group of related speeches'''
    
    class Meta:
        ordering = ['seq']

    seq = models.IntegerField(default=0)
    
    @cached_property
    def _speeches(self):
        return list(self.speeches.all())

    @cached_property
    def work(self):
        return self._speeches[0].work if self._speeches else None
                
    @cached_property
    def speakers(self):
        s=set()
        for sp in self._speeches: s.update(sp.spkr.all())
        return tuple(s)    

    @cached_property
    def addressees(self):
        s=set()
        for sp in self._speeches: s.update(sp.addr.all())
        return tuple(s) 

    def get_spkr_str(self, sep=", "):
        '''Return speaker list as a string'''
        return sep.join(sorted(map(str, self.speakers)))    

    def get_addr_str(self, sep=", "):
        '''Return addressee list as a string'''
        return sep.join(sorted(map(str, self.addressees)))        

    def get_chars_str(self, sep=", "):
        '''Return list of all participants as a string'''
        chars = set(self.speakers + self.addressees)
        return sep.join(sorted(map(str, chars)))
                
    def get_urn(self):
        '''Return CTS URN for the whole cluster'''
            
        work = self.work
        if work is None or work.urn is None:
            return None
        
        urn = work.urn
        l_fi = self._speeches[0].l_fi
        l_la = self._speeches[-1].l_la
        
        return f'{urn}:{l_fi}-{l_la}'

    def get_loc_str(self):
        '''Return line range of conversation as a string'''

        work = self.work
        if work is None:
            return None
        
        long_name = work.get_long_name()
        l_fi = self._speeches[0].l_fi
        l_la = self._speeches[-1].l_la
        return f'{long_name} {l_fi}–{l_la}'
        

class Speech(PublicIdModel):
    '''A direct speech instance'''
    
    class SpeechType(models.TextChoices):
        SOLILOQUY = ('S', 'Soliloquy')
        MONOLOGUE = ('M', 'Monologue')
        DIALOGUE = ('D', 'Dialogue')
        GENERAL = ('G', 'General')
    
    cluster = models.ForeignKey(SpeechCluster, related_name='speeches', on_delete=models.CASCADE)
    work = models.ForeignKey(Work, on_delete=models.PROTECT)
    type = models.CharField(max_length=1, choices=SpeechType.choices)
    seq = models.IntegerField()
    l_fi = models.CharField('first line', max_length=16)
    l_la = models.CharField('last line', max_length=16)
    spkr = models.ManyToManyField(CharacterInstance, related_name='speeches')
    addr = models.ManyToManyField(CharacterInstance, related_name='addresses', blank=True, default="")
    spkr_notes = models.CharField(max_length=256, blank=True, default="")
    addr_notes = models.CharField(max_length=256, blank=True, default="")
    part = models.IntegerField()
    level = models.IntegerField(default=0)
    notes = models.CharField(max_length=256, blank=True, default="")
    
    class Meta:
        ordering = ['work', 'seq']
    
    def __str__(self):
        return f'{self.work} {self.l_fi}-{self.l_la}'
        
    def get_urn(self):
        '''Return CTS URN for the whole speech'''
        if self.work.urn:
            return f'{self.work.urn}:{self.l_fi}-{self.l_la}'
        
    def get_spkr_str(self):
        '''Return speaker list as a string'''
        return ', '.join([str(s) for s in self.spkr.all()])
    
    def get_addr_str(self):
        '''Return speaker list as a string'''
        return ', '.join([str(s) for s in self.addr.all()])
        
    def get_short_type(self):
        '''Return one-char type designation'''
        t = self.type
        if t == 'D' or t == 'G':
            t += str(self.part)
        return t


class SpeechTag(PublicIdModel):
    '''A category tag for speeches'''

    class TagType(models.TextChoices):
        CHALLENGE = ('cha', 'Challenge')
        COMMAND = ('com', 'Command')
        CONSOLATION = ('con', 'Consolation')
        DELIBERATION = ('del', 'Deliberation')
        DESIRE = ('des', 'Desire and Wish')
        EXHORTATION = ('exh', 'Exhortation and Self-Exhortation')
        FAREWELL = ('far', 'Farewell')
        GREETING = ('gre', 'Greeting and Reception')
        INFORMATION = ('inf', 'Information and Description')
        INVITATION = ('inv', 'Invitation')
        INSTRUCTION = ('ins', 'Instruction')
        LAMENT = ('lam', 'Lament')
        PRAISE = ('lau', 'Praise and Laudation')
        MESSAGE = ('mes', 'Message')
        NARRATION = ('nar', 'Narration')
        PROPHESY = ('ora', 'Prophecy, Oracular Speech, and Interpretation')
        PERSUASION = ('per', 'Persuasion')
        PRAYER = ('pra', 'Prayer')
        QUESTION = ('que', 'Question')
        REQUEST = ('req', 'Request')
        REPLY = ('res',	'Reply to Question')
        TAUNT = ('tau', 'Taunt')
        THREAT = ('thr', 'Threat')
        VITUPERATION = ('vit', 'Vituperation')
        VOW = ('vow', 'Promise and Oath')
        WARNING = ('war', 'Warning')
        UNDEFINED = ('und', 'Undefined')

    type = models.CharField(max_length=3, choices=TagType.choices, 
                                default=TagType.UNDEFINED)
    doubt = models.BooleanField(default=False)
    notes = models.CharField(max_length=128, blank=True, default="")
    speech = models.ForeignKey(Speech, on_delete=models.CASCADE, related_name='tags')
