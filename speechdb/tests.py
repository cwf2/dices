from django.test import TestCase
from rest_framework.test import APIClient

from speechdb.models import (Author, Character, CharacterInstance, Speech,
                             SpeechCluster, Work)
from speechdb.serializers import SpeechSerializer


class SerializerDepthTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        author = Author.objects.create(name='Homer')
        work = Work.objects.create(title='Iliad', author=author, lang='greek')
        char = Character.objects.create(name='Achilles')
        inst = CharacterInstance.objects.create(
            name='Achilles', display='Achilles', char=char, context='Iliad')
        cluster = SpeechCluster.objects.create(seq=1)
        speech = Speech.objects.create(
            cluster=cluster, work=work, type='M', seq=1, l_fi='1', l_la='2',
            part=1)
        speech.spkr.add(inst)

    def test_depth_does_not_leak_between_instances(self):
        default_depth = SpeechSerializer.Meta.depth
        SpeechSerializer(depth=0)
        self.assertEqual(SpeechSerializer.Meta.depth, default_depth)

    def test_depth_override_applies_to_that_instance(self):
        self.assertEqual(SpeechSerializer(depth=0).Meta.depth, 0)
        self.assertEqual(SpeechSerializer(depth=1).Meta.depth, 1)

    def test_depth_query_param_does_not_flatten_later_requests(self):
        client = APIClient()
        flat = client.get('/api/speeches/?depth=0').json()
        self.assertIsInstance(flat['results'][0]['work'], int)

        nested = client.get('/api/speeches/').json()
        self.assertIsInstance(nested['results'][0]['work'], dict)

    def test_depth_still_honored_when_fields_are_restricted(self):
        serializer = SpeechSerializer(fields=['id', 'work'], depth=0)
        self.assertEqual(set(serializer.fields), {'id', 'work'})
        self.assertEqual(serializer.fields['work'].__class__.__name__,
                         'PrimaryKeyRelatedField')
