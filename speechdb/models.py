from django.db import models

class Author(models.Model):
    '''An ancient author'''
    
    name = models.CharField(max_length=64)
    wd = models.CharField('WikiData ID', max_length=32)
    
    def __str__(self):
        return self.name


class Work(models.Model):
    '''An epic text'''
    
    title = models.CharField(max_length=64)
    urn = models.CharField(max_length=128)
    author = models.ForeignKey(Author, on_delete=models.PROTECT)
    
    def __str__(self):
        return f'{self.author.name} {self.title}'


class Character(models.Model):
    '''An epic character'''
    
    name = models.CharField(max_length=64)
    wd = models.CharField('WikiData ID', max_length=32)
    manto = models.CharField('MANTO ID', max_length=32)

    def __str__(self):
        return self.name


class Speech(models.Model):
    '''A direct speech instance'''
    
    work = models.ForeignKey(Work, on_delete=models.PROTECT)
    l_fi = models.CharField('first line', max_length=8)
    l_la = models.CharField('last line', max_length=8)
    
    def __str__(self):
        return f'{self.work} {self.l_fi}-{self.l_la}'


class CharacterInstance(models.Model):
    '''A character engaged in a speech'''
    role_choices = [
        ('SPKR', 'speaker'), 
        ('ADDR', 'addressee'),
    ]
    
    char = models.ForeignKey(Character, related_name='character', 
            on_delete=models.PROTECT)
    disg = models.ForeignKey(Character, related_name='disguise', 
            blank=True, null=True, on_delete=models.PROTECT)
    role = models.CharField(max_length=4, choices=role_choices)
    speech = models.ForeignKey(Speech, on_delete=models.PROTECT)
    
    def __str__(self):
        name = self.char.name
        if self.disg is not None:
            name += '/' + self.disg.name
        return name