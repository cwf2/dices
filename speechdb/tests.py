import csv
import hashlib
import io
import json
import tempfile
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from rest_framework.test import APIClient

from speechdb.models import (Author, Character, CharacterInstance, Metadata,
                             Speech, SpeechCluster, SpeechTag, Work)
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


class ExportArchiveTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        author = Author.objects.create(name='Homer', wd='Q6691')
        cls.work = Work.objects.create(title='Iliad', author=author, lang='greek')
        cls.char = Character.objects.create(
            name='Achilles', notes='Ἀχιλλεύς\t"best of the Achaeans"\nline two')
        cls.achilles = CharacterInstance.objects.create(
            name='Achilles', display='Achilles', char=cls.char, context='Iliad')
        cls.anon = CharacterInstance.objects.create(
            name='crowd', display='crowd', number='collective', anon=True, context='Iliad')
        cluster = SpeechCluster.objects.create(seq=7)
        cls.outer = Speech.objects.create(
            cluster=cluster, work=cls.work, type='M', seq=1, l_fi='1.1', l_la='1.9', part=1)
        cls.inner = Speech.objects.create(
            cluster=cluster, work=cls.work, type='M', seq=2, l_fi='1.3', l_la='1.4',
            part=1, level=1, embedded_in=cls.outer)
        cls.outer.spkr.add(cls.achilles)
        cls.outer.addr.add(cls.anon)
        SpeechTag.objects.create(speech=cls.outer, type='thr', doubt=True)

    def export(self, *args):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        call_command('export_archive', tmp.name, *args, stdout=open('/dev/null', 'w'))
        return Path(tmp.name)

    def read(self, path, delimiter='\t'):
        with open(path, newline='', encoding='utf-8') as f:
            return list(csv.DictReader(f, delimiter=delimiter))

    def test_writes_expected_files(self):
        out = self.export()
        names = {p.name for p in out.iterdir()}
        self.assertEqual(names, {
            'metadata.tsv', 'authors.tsv', 'works.tsv', 'characters.tsv',
            'instances.tsv', 'clusters.tsv', 'speeches.tsv', 'tags.tsv',
            'speech_spkr.tsv', 'speech_addr.tsv', 'speeches_flat.tsv', 'README.txt'})

    def test_every_model_field_is_a_column(self):
        out = self.export()
        for filename, model in [('speeches.tsv', Speech), ('instances.tsv', CharacterInstance),
                                ('characters.tsv', Character), ('works.tsv', Work)]:
            with open(out / filename, encoding='utf-8') as f:
                header = f.readline().rstrip('\n').split('\t')
            self.assertEqual(header, [f.attname for f in model._meta.concrete_fields])

    def test_ids_and_relations_are_preserved(self):
        out = self.export()
        speeches = {r['id']: r for r in self.read(out / 'speeches.tsv')}
        inner = speeches[str(self.inner.id)]
        self.assertEqual(inner['public_id'], self.inner.public_id)
        self.assertEqual(inner['embedded_in_id'], str(self.outer.id))
        self.assertEqual(inner['cluster_id'], str(self.outer.cluster_id))
        self.assertEqual(speeches[str(self.outer.id)]['embedded_in_id'], '')

        inst = {r['id']: r for r in self.read(out / 'instances.tsv')}
        self.assertEqual(inst[str(self.achilles.id)]['char_id'], str(self.char.id))
        self.assertEqual(inst[str(self.anon.id)]['char_id'], '')
        self.assertEqual(inst[str(self.anon.id)]['anon'], 'true')
        self.assertEqual(inst[str(self.achilles.id)]['anon'], 'false')

    def test_many_to_many_links(self):
        out = self.export()
        spkr = self.read(out / 'speech_spkr.tsv')
        addr = self.read(out / 'speech_addr.tsv')
        self.assertEqual(spkr, [{'speech_id': str(self.outer.id),
                                 'characterinstance_id': str(self.achilles.id)}])
        self.assertEqual(addr, [{'speech_id': str(self.outer.id),
                                 'characterinstance_id': str(self.anon.id)}])

    def test_greek_and_awkward_characters_round_trip(self):
        out = self.export()
        chars = self.read(out / 'characters.tsv')
        self.assertEqual(chars[0]['notes'], self.char.notes)

    def test_csv_format(self):
        out = self.export('--format', 'csv')
        chars = self.read(out / 'characters.csv', delimiter=',')
        self.assertEqual(chars[0]['notes'], self.char.notes)

    def test_flat_file_is_readable(self):
        out = self.export()
        rows = {r['public_id']: r for r in self.read(out / 'speeches_flat.tsv')}
        outer = rows[self.outer.public_id]
        self.assertEqual(outer['work'], 'Iliad')
        self.assertEqual(outer['speakers'], 'Achilles')
        self.assertEqual(outer['addressees'], 'crowd')
        self.assertEqual(outer['tags'], 'thr?')
        self.assertEqual(rows[self.inner.public_id]['embedded_in'], self.outer.public_id)

    def test_readme_lists_files_and_counts(self):
        out = self.export()
        text = (out / 'README.txt').read_text(encoding='utf-8')
        self.assertIn('Digital Initiative for Classics: Epic Speeches', text)
        self.assertIn('speeches.tsv  (2 rows)', text)
        self.assertIn('speech_spkr.tsv  (1 rows)', text)
        self.assertNotIn('Creatures and Episodes', text)
        self.assertFalse((self.export('--no-readme') / 'README.txt').exists())


class ReleaseStampTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        author = Author.objects.create(name='Homer')
        cls.work = Work.objects.create(title='Iliad', author=author, lang='greek')
        Metadata.objects.create(name='version', value='1.1')
        Metadata.objects.create(name='date', value='2025-11-16 13:55:55 -0400')

    def export(self, *args):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        out = io.StringIO()
        call_command('export_archive', tmp.name, *args, stdout=out)
        return Path(tmp.name), out.getvalue()

    def meta(self):
        return dict(Metadata.objects.values_list('name', 'value'))

    def test_plain_export_does_not_change_the_database(self):
        before = self.meta()
        self.export()
        self.assertEqual(self.meta(), before)

    def test_release_stamps_metadata(self):
        out, _ = self.export('--release', '1.2')
        meta = self.meta()
        self.assertEqual(meta['version'], '1.2')
        self.assertNotEqual(meta['date'], '2025-11-16 13:55:55 -0400')
        self.assertEqual(meta['doi'], '10.5683/SP3/N8LS2Y')
        self.assertEqual(meta['export-format'], '1')
        self.assertRegex(meta['content-sha256'], r'^[0-9a-f]{64}$')
        self.assertEqual(Metadata.objects.filter(name='version').count(), 1)

    def test_metadata_file_carries_the_new_stamp(self):
        out, _ = self.export('--release', '1.2')
        with open(out / 'metadata.tsv', newline='', encoding='utf-8') as f:
            rows = {r['name']: r['value'] for r in csv.DictReader(f, delimiter='\t')}
        self.assertEqual(rows['version'], '1.2')
        self.assertEqual(rows['content-sha256'], self.meta()['content-sha256'])

    def test_hash_matches_the_documented_definition(self):
        out, _ = self.export('--release', '1.2')
        digest = hashlib.sha256()
        for name in ['authors', 'works', 'characters', 'instances', 'clusters',
                     'speeches', 'speech_spkr', 'speech_addr', 'tags']:
            digest.update(f'{name}.tsv'.encode() + b'\0')
            digest.update((out / f'{name}.tsv').read_bytes() + b'\0')
        self.assertEqual(digest.hexdigest(), self.meta()['content-sha256'])

    def test_stamping_does_not_change_the_hash(self):
        first, _ = self.export()
        second, _ = self.export('--release', '1.2')
        third, _ = self.export()
        hashes = []
        for out in (first, second, third):
            text = (out / 'README.txt').read_text(encoding='utf-8')
            hashes.append([l for l in text.splitlines() if l.startswith('Content hash:')][0])
        self.assertEqual(len(set(hashes)), 1)

    def test_status_reports_changes_since_release(self):
        self.export('--release', '1.2')
        out, _ = self.export()
        self.assertIn('Identical to release 1.2',
                      (out / 'README.txt').read_text(encoding='utf-8'))
        Author.objects.create(name='Virgil')
        out, console = self.export()
        self.assertIn('Differs from release 1.2',
                      (out / 'README.txt').read_text(encoding='utf-8'))
        self.assertIn('Differs from release 1.2', console)

    def test_verify_accepts_a_release_and_rejects_tampering(self):
        out, _ = self.export('--release', '1.2')
        report = io.StringIO()
        call_command('export_archive', str(out), '--verify', stdout=report)
        self.assertIn('OK', report.getvalue())

        works = out / 'works.tsv'
        works.write_text(works.read_text(encoding='utf-8') + 'tampered\n', encoding='utf-8')
        with self.assertRaisesMessage(CommandError, 'Content hash mismatch'):
            call_command('export_archive', str(out), '--verify', stdout=io.StringIO())

    def test_verify_requires_a_recorded_hash(self):
        out, _ = self.export()
        with self.assertRaisesMessage(CommandError, 'no content-sha256'):
            call_command('export_archive', str(out), '--verify', stdout=io.StringIO())


class ImportSpeechesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        from django.contrib.auth import get_user_model
        cls.user = get_user_model().objects.create_user('editor')
        author = Author.objects.create(name='Dracontius')
        cls.work = Work.objects.create(title='Helen', author=author, lang='latin')
        other = Work.objects.create(title='Medea', author=author, lang='latin')
        cls.paris_char = Character.objects.create(name='Paris')
        cls.priam_char = Character.objects.create(name='Priam')
        cls.paris = CharacterInstance.objects.create(
            name='Paris', display='Paris', char=cls.paris_char,
            context='Dracontius Helen')
        cluster = SpeechCluster.objects.create(seq=1)
        cls.old = Speech.objects.create(
            cluster=cluster, work=cls.work, type='M', seq=1, l_fi='8.91',
            l_la='8.102', part=1)
        cls.old.spkr.add(cls.paris)
        cls.old.addr.add(cls.paris)
        SpeechTag.objects.create(speech=cls.old, type='exh')
        # a cluster seq already taken by another work
        taken = SpeechCluster.objects.create(seq=500)
        Speech.objects.create(cluster=taken, work=other, type='M', seq=1,
                              l_fi='1', l_la='2', part=1)

    def batch(self, **changes):
        data = {
            'instances': [
                dict(name='Paris', status=f'EXISTS {self.paris.public_id}', char='',
                     being='', number='', gender='', anon=''),
                dict(name='Priam', status='new', char=self.priam_char.public_id,
                     being='mortal', number='individual', gender='male', anon='no'),
                dict(name='Trojans', status='new', char='', being='mortal',
                     number='collective', gender='x', anon='yes'),
            ],
            'speeches': [
                dict(status=f'EXISTS {self.old.public_id}', seq='1', l_fi='8.91',
                     l_la='8.102', type='M', cluster='101', part='1', level='0',
                     embedded_in='', spkr='Paris', addr='Priam; Trojans',
                     spkr_notes='', addr_notes='', notes='', tags='gre, inf'),
                dict(status='new', seq='2', l_fi='8.221', l_la='8.229', type='D',
                     cluster='102', part='1', level='0', embedded_in='',
                     spkr='Priam', addr='Paris', spkr_notes='', addr_notes='',
                     notes='', tags='que, ins'),
                dict(status='new', seq='3', l_fi='8.225', l_la='8.226', type='M',
                     cluster='103', part='1', level='1', embedded_in='8.221',
                     spkr='Trojans', addr='Trojans', spkr_notes='', addr_notes='',
                     notes='imagined', tags='vit'),
                dict(status='skip', seq='4', l_fi='8.300', l_la='8.301', type='X',
                     cluster='x', part='', level='', embedded_in='', spkr='', addr='',
                     spkr_notes='', addr_notes='', notes='', tags=''),
            ],
        }
        for path, value in changes.items():
            kind, i, field = path.split('__')
            data[kind][int(i)][field] = value
        f = tempfile.NamedTemporaryFile('w', suffix='.json', delete=False)
        json.dump(data, f)
        f.close()
        self.addCleanup(Path(f.name).unlink)
        return f.name

    def run_import(self, path, apply=True):
        out = io.StringIO()
        args = [path, '--work', self.work.public_id, '--user', 'editor']
        if apply:
            args.append('--apply')
        call_command('import_speeches', *args, stdout=out)
        return out.getvalue()

    def test_dry_run_writes_nothing(self):
        from django.contrib.admin.models import LogEntry
        out = self.run_import(self.batch(), apply=False)
        self.assertIn('DRY RUN', out)
        self.assertEqual(Speech.objects.filter(work=self.work).count(), 1)
        self.assertFalse(CharacterInstance.objects.filter(name='Priam').exists())
        self.assertEqual(LogEntry.objects.count(), 0)

    def test_apply_creates_speeches_instances_and_clusters(self):
        self.run_import(self.batch())
        new = Speech.objects.get(work=self.work, l_fi='8.221')
        self.assertEqual(new.cluster.seq, 102)
        self.assertEqual([i.name for i in new.spkr.all()], ['Priam'])
        self.assertEqual(new.spkr.get().char, self.priam_char)
        self.assertEqual(new.spkr.get().context, 'Dracontius Helen')
        self.assertEqual(sorted(t.type for t in new.tags.all()), ['ins', 'que'])
        embedded = Speech.objects.get(work=self.work, l_fi='8.225')
        self.assertEqual(embedded.embedded_in, new)
        self.assertTrue(embedded.spkr.get().anon)
        self.assertFalse(Speech.objects.filter(l_fi='8.300').exists())

    def test_existing_speech_is_brought_in_line(self):
        self.run_import(self.batch())
        self.old.refresh_from_db()
        self.assertEqual(self.old.cluster.seq, 101)
        self.assertEqual(sorted(i.name for i in self.old.addr.all()), ['Priam', 'Trojans'])
        self.assertEqual(sorted(t.type for t in self.old.tags.all()), ['gre', 'inf'])

    def test_changes_are_logged(self):
        from django.contrib.admin.models import LogEntry
        self.run_import(self.batch())
        entries = LogEntry.objects.filter(user=self.user)
        self.assertTrue(entries.exists())
        self.assertTrue(all(e.change_message.startswith('import_speeches:') for e in entries))

    def test_rerun_changes_nothing(self):
        from django.contrib.admin.models import LogEntry
        path = self.batch()
        self.run_import(path)
        before = (Speech.objects.count(), CharacterInstance.objects.count(),
                  SpeechCluster.objects.count(), LogEntry.objects.count())
        out = self.run_import(path)
        self.assertIn('0 changes logged', out)
        self.assertEqual(before, (Speech.objects.count(), CharacterInstance.objects.count(),
                                  SpeechCluster.objects.count(), LogEntry.objects.count()))

    def test_problems_are_all_reported_and_nothing_written(self):
        path = self.batch(speeches__1__tags='que, xyz', speeches__1__addr='Priamus',
                          speeches__2__cluster='500')
        with self.assertRaises(CommandError) as cm:
            self.run_import(path)
        msg = str(cm.exception)
        self.assertIn("bad tag 'xyz'", msg)
        self.assertIn("'Priamus' not listed", msg)
        self.assertIn('used by another work', msg)
        self.assertEqual(Speech.objects.filter(work=self.work).count(), 1)

    def test_embedded_speech_needs_a_parent(self):
        path = self.batch(speeches__2__embedded_in='')
        with self.assertRaisesRegex(CommandError, 'level > 0 but no embedded_in'):
            self.run_import(path)

    def test_unknown_work_or_user(self):
        path = self.batch()
        with self.assertRaisesRegex(CommandError, 'no Work'):
            call_command('import_speeches', path, '--work', 'ZZZZ', '--user', 'editor')
        with self.assertRaisesRegex(CommandError, 'no user'):
            call_command('import_speeches', path, '--work', self.work.public_id,
                         '--user', 'nobody')


class ContextNameTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        from django.contrib.auth import get_user_model
        cls.admin = get_user_model().objects.create_superuser('boss', password='x')
        cls.homer = Author.objects.create(name='Homer')
        cls.iliad = Work.objects.create(title='Iliad', author=cls.homer, lang='greek')
        anon = Author.objects.create(name='Anonymous')
        cls.orphic = Work.objects.create(title='Orphic Argonautica', author=anon, lang='greek')

    def test_context_name_is_author_space_title(self):
        self.assertEqual(self.iliad.get_context_name(), 'Homer Iliad')
        self.assertEqual(self.orphic.get_context_name(), 'Anonymous Orphic Argonautica')
        # display name is unchanged
        self.assertEqual(self.iliad.get_long_name(), 'Homer, Iliad')

    def test_admin_add_instance_builds_context_from_work(self):
        self.client.force_login(self.admin)
        r = self.client.get('/admin/speechdb/characterinstance/add/',
                            {'work': self.iliad.pk})
        self.assertEqual(r.context['adminform'].form.initial['context'], 'Homer Iliad')
        r = self.client.get('/admin/speechdb/characterinstance/add/', {'work': 'junk'})
        self.assertNotIn('context', r.context['adminform'].form.initial)


class AuditContextsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        from django.contrib.auth import get_user_model
        cls.user = get_user_model().objects.create_user('editor')
        author = Author.objects.create(name='Nonnus')
        cls.work = Work.objects.create(title='Dionysiaca', author=author, lang='greek')
        other = Work.objects.create(title='Paraphrase', author=author, lang='greek')

        def inst(name, context):
            return CharacterInstance.objects.create(name=name, display=name, context=context)
        cls.good = inst('Dionysus', 'Nonnus Dionysiaca')
        cls.bad = inst('shores of Naxos', 'Dionysiaca')
        cls.comma = inst('Ariadne', 'Nonnus, Dionysiaca')
        cls.multi = inst('Jesus', 'Nonnus Dionysiaca')
        cls.orphan = inst('nobody', 'Nonnus Dionysiaca')
        for i, (w, spkr, addr) in enumerate([(cls.work, cls.good, cls.bad),
                                              (cls.work, cls.comma, cls.multi),
                                              (other, cls.multi, cls.multi)]):
            s = Speech.objects.create(cluster=SpeechCluster.objects.create(seq=i),
                                      work=w, type='M', seq=i, l_fi='1', l_la='2', part=1)
            s.spkr.add(spkr)
            s.addr.add(addr)

    def audit(self, *args):
        out = io.StringIO()
        call_command('audit_contexts', *args, stdout=out)
        return out.getvalue()

    def test_report_finds_each_kind_and_changes_nothing(self):
        out = self.audit()
        self.assertIn('5 instances: 1 ok, 2 mismatch, 1 multi-work, 1 orphan', out)
        self.assertIn("'Dionysiaca' -> 'Nonnus Dionysiaca'", out)
        self.bad.refresh_from_db()
        self.assertEqual(self.bad.context, 'Dionysiaca')

    def test_apply_fixes_mismatches_only_and_logs(self):
        from django.contrib.admin.models import LogEntry
        self.audit('--apply', '--user', 'editor')
        for i in (self.bad, self.comma, self.multi, self.orphan):
            i.refresh_from_db()
        self.assertEqual(self.bad.context, 'Nonnus Dionysiaca')
        self.assertEqual(self.comma.context, 'Nonnus Dionysiaca')
        self.assertEqual(LogEntry.objects.filter(user=self.user).count(), 2)
        self.assertIn('0 mismatch', self.audit())

    def test_apply_needs_user(self):
        with self.assertRaisesRegex(CommandError, '--apply needs --user'):
            self.audit('--apply')


class StableOrderingTests(TestCase):
    def test_paging_through_same_named_instances_sees_each_once(self):
        # more than one page (PAGE_SIZE 200) of instances that tie on name
        CharacterInstance.objects.bulk_create(
            [CharacterInstance(name='Hermes', display='Hermes', context='x',
                               public_id=f'{n:04X}') for n in range(250)])
        client = APIClient()
        seen = []
        for page in (1, 2):
            r = client.get('/api/instances/', {'page': page}).json()
            seen += [i['id'] for i in r['results']]
        self.assertEqual(sorted(seen), sorted(CharacterInstance.objects.values_list('id', flat=True)))

    def test_every_default_ordering_ends_with_id(self):
        from speechdb.models import Author, Character, Speech, SpeechCluster, Work
        for model in (Author, Work, Character, CharacterInstance, SpeechCluster, Speech):
            self.assertEqual(model._meta.ordering[-1], 'id', model.__name__)


class RemoveWorkTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        from django.contrib.auth import get_user_model
        cls.user = get_user_model().objects.create_user('editor')
        cls.author = Author.objects.create(name='Dracontius')
        cls.gone = Work.objects.create(title='Verba Herculis', author=cls.author, lang='latin')
        cls.kept = Work.objects.create(title='Hylas', author=cls.author, lang='latin')
        cls.char = Character.objects.create(name='Heracles')

        def inst(name, ctx):
            return CharacterInstance.objects.create(name=name, display=name, char=cls.char,
                                                    context=ctx)
        cls.minerva = inst('Minerva', 'Dracontius Verba Herculis')
        cls.hercules = inst('Hercules', 'Dracontius Verba Herculis')
        cls.shared = inst('Venus', 'Dracontius Hylas')   # also used in the kept work

        def speech(work, seq, spkr, addr, **kw):
            s = Speech.objects.create(cluster=kw.pop('cluster', None) or
                                      SpeechCluster.objects.create(seq=seq),
                                      work=work, type='M', seq=seq, l_fi=f'{seq}',
                                      l_la=f'{seq}', part=1, **kw)
            s.spkr.add(spkr)
            s.addr.add(addr)
            return s
        cls.s1 = speech(cls.gone, 1, cls.minerva, cls.hercules)
        SpeechTag.objects.create(speech=cls.s1, type='ins')
        cls.s2 = speech(cls.gone, 2, cls.hercules, cls.shared, level=1, embedded_in=cls.s1)
        cls.s3 = speech(cls.kept, 3, cls.shared, cls.shared)

    def remove(self, *extra):
        out = io.StringIO()
        call_command('remove_work', self.gone.public_id, '--user', 'editor', *extra, stdout=out)
        return out.getvalue()

    def test_dry_run_changes_nothing(self):
        out = self.remove()
        self.assertIn('DRY RUN', out)
        self.assertTrue(Work.objects.filter(pk=self.gone.pk).exists())
        self.assertEqual(Speech.objects.count(), 3)

    def test_apply_removes_work_speeches_clusters_and_own_instances(self):
        self.remove('--apply')
        self.assertFalse(Work.objects.filter(pk=self.gone.pk).exists())
        self.assertEqual(list(Speech.objects.all()), [self.s3])
        self.assertEqual(SpeechCluster.objects.count(), 1)
        self.assertEqual(SpeechTag.objects.count(), 0)
        self.assertEqual(set(CharacterInstance.objects.all()), {self.shared})
        self.assertTrue(Character.objects.filter(pk=self.char.pk).exists())
        self.assertTrue(Author.objects.filter(pk=self.author.pk).exists())

    def test_deletions_are_logged_with_recoverable_data(self):
        from django.contrib.admin.models import DELETION, LogEntry
        self.remove('--apply', '--reason', 'out of scope')
        entries = LogEntry.objects.filter(user=self.user, action_flag=DELETION)
        self.assertEqual(entries.count(), 7)   # 2 speeches, 2 clusters, 2 instances, work
        speech_entry = entries.get(object_id=str(self.s1.pk),
                                   content_type__model='speech')
        msg = speech_entry.change_message
        self.assertTrue(msg.startswith('remove_work (out of scope): '))
        data = json.loads(msg.split(': ', 1)[1])
        self.assertEqual(data['fields']['l_fi'], '1')
        self.assertEqual(data['tags'], ['ins'])
        self.assertTrue(data['spkr'][0].startswith('Minerva'))

    def test_refuses_if_another_work_embeds_in_it(self):
        self.s3.embedded_in = self.s1
        self.s3.save()
        with self.assertRaisesRegex(CommandError, 'embedded in this one'):
            self.remove('--apply')
        self.assertTrue(Work.objects.filter(pk=self.gone.pk).exists())
