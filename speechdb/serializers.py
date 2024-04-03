from rest_framework import serializers
from speechdb.models import Metadata
from speechdb.models import Author, Work, Character, CharacterInstance, Speech, SpeechCluster, SpeechTag


class DynamicModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Don't pass the extra args up to the superclass
        fields = kwargs.pop('fields', None)
        depth = kwargs.pop('depth', -1)

        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)

        if depth >= 0:
            self.Meta.depth = depth


class MetadataSerializer(DynamicModelSerializer):
    class Meta:
        model = Metadata
        fields = '__all__'


class AuthorSerializer(DynamicModelSerializer):
    class Meta:
        model = Author
        fields = '__all__'
        
        
class WorkSerializer(DynamicModelSerializer):
    class Meta:
        model = Work
        fields = '__all__'
        depth = 2


class CharacterSerializer(DynamicModelSerializer):
    class Meta:
        model = Character
        fields = '__all__'


class CharacterInstanceSerializer(DynamicModelSerializer):
    class Meta:
        model = CharacterInstance
        fields = '__all__'
        depth = 1

class SpeechTagSerializer(DynamicModelSerializer):
    class Meta:
        model = SpeechTag
        fields = ['type', 'doubt']
        depth = 1

class SpeechSerializer(DynamicModelSerializer):
    tags = SpeechTagSerializer(many=True)
    
    class Meta:
        model = Speech
        fields = '__all__'
        depth = 3

class SpeechClusterSerializer(DynamicModelSerializer):
    speeches = SpeechSerializer(many=True, fields=['id'])
    
    class Meta:
        model = SpeechCluster
        fields = '__all__'
        depth = 3
