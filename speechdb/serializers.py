from rest_framework import serializers
from speechdb.models import Author, Work, Character, CharacterInstance, Speech, SpeechCluster

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['id', 'name', 'wd', 'urn']
        
        
class WorkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Work
        fields = ['id', 'title', 'wd', 'urn', 'author', 'lang']
        depth = 2


class CharacterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Character
        fields = ['id', 'name', 'being', 'number', 'gender', 'wd', 'manto']


class CharacterInstanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CharacterInstance
        fields = ['id', 'name', 'being', 'number', 'gender', 'anon',
                    'char', 'disg', 'context']
        depth = 1


class SpeechSerializer(serializers.ModelSerializer):
    class Meta:
        model = Speech
        fields = ['id', 'work', 'l_fi', 'l_la', 'seq', 'spkr', 'addr', 
                    'type', 'cluster', 'part']
        depth = 3

class SpeechClusterSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpeechCluster
        fields = ['id']
        depth = 3
