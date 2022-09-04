from rest_framework import serializers
from speechdb.models import Metadata
from speechdb.models import Author, Work, Character, CharacterInstance, Speech, SpeechCluster

class MetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Metadata
        fields = '__all__'


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = '__all__'
        
        
class WorkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Work
        fields = '__all__'
        depth = 2


class CharacterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Character
        fields = '__all__'


class CharacterInstanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CharacterInstance
        fields = '__all__'
        depth = 1


class SpeechSerializer(serializers.ModelSerializer):
    class Meta:
        model = Speech
        fields = '__all__'
        depth = 3

class SpeechClusterSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpeechCluster
        fields = '__all__'
        depth = 3
