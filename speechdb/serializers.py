from rest_framework import serializers
from speechdb.models import Author, Work, Character, CharacterInstance, Speech, SpeechCluster

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['id', 'name', 'wd', 'urn']
        
        
class WorkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Work
        fields = ['id', 'title', 'wd', 'urn', 'author']


class CharacterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Character
        fields = ['id', 'name', 'being', 'type', 'wd', 'manto']


class CharacterInstanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CharacterInstance
        fields = ['id', 'char', 'disg', 'context']


class SpeechSerializer(serializers.ModelSerializer):
    class Meta:
        model = Speech
        fields = ['id', 'cluster', 'seq', 'l_fi', 'l_la', 'spkr', 'addr', 'part']


class SpeechClusterSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpeechCluster
        fields = ['id', 'type', 'work', ]
