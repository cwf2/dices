'''Load a reviewed batch of speeches into one Work.

    python manage.py import_speeches batch.json --work B728 --user chris
    python manage.py import_speeches batch.json --work B728 --user chris --apply

Without --apply this is a dry run: everything is written inside a
transaction and then rolled back, so the printed list of changes is exactly
what --apply would do.

The batch is a JSON object with two lists, "instances" and "speeches" (all
values are strings, as they come out of a spreadsheet):

  instances: name, status, char, being, number, gender, anon
    status   "new", or "EXISTS <public_id>" for an instance already in the DB
    char     Character public_id, or "" for an anonymous instance
    anon     "yes" / "no"
    (being/number/gender/anon are only used when the instance is created)

  speeches: status, seq, l_fi, l_la, type, cluster, part, level,
            embedded_in, spkr, addr, spkr_notes, addr_notes, notes, tags
    status       "new", "skip", or "EXISTS <public_id>"
    cluster      SpeechCluster seq (speeches sharing it share a cluster)
    embedded_in  l_fi of the enclosing speech in the same work, or ""
    spkr, addr   instance names separated by ";" (each must be listed
                 under "instances")
    tags         SpeechTag codes separated by ","

Rules:
  - Everything is validated before anything is written; any problem stops
    the run with a list of all problems.
  - Safe to re-run: new instances are matched by (name, context) and new
    speeches by (work, l_fi, l_la); anything already present is left alone.
  - "EXISTS" speeches are brought in line with the batch: cluster seq, type,
    speakers, addressees and tags.
  - Every change is recorded in the admin history (LogEntry) under --user,
    prefixed "import_speeches:".
'''
import json

from django.contrib.admin.models import ADDITION, CHANGE, LogEntry
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from speechdb.models import (Character, CharacterInstance, Speech,
                             SpeechCluster, SpeechTag, Work)

TYPES = {c for c, _ in Speech.SpeechType.choices}
TAGS = {c for c, _ in SpeechTag.TagType.choices}
BEING = {c for c, _ in Character.CharacterBeing.choices}
NUMBER = {c for c, _ in Character.CharacterNumber.choices}
GENDER = {c for c, _ in Character.CharacterGender.choices}

INSTANCE_FIELDS = ['name', 'status', 'char', 'being', 'number', 'gender', 'anon']
SPEECH_FIELDS = ['status', 'seq', 'l_fi', 'l_la', 'type', 'cluster', 'part',
                 'level', 'embedded_in', 'spkr', 'addr', 'spkr_notes',
                 'addr_notes', 'notes', 'tags']


class DryRun(Exception):
    pass


def names(s):
    return [n.strip() for n in s.split(';') if n.strip()]


def tag_list(s):
    return [t.strip() for t in s.split(',') if t.strip()]


def existing_id(status):
    '''"EXISTS 1A2B" -> "1A2B"; anything else -> None'''
    parts = status.split()
    if len(parts) == 2 and parts[0] == 'EXISTS':
        return parts[1]
    return None


class Command(BaseCommand):
    help = 'Load a reviewed JSON batch of speeches and instances into one Work (dry run unless --apply)'

    def add_arguments(self, parser):
        parser.add_argument('batch', help='JSON file with "instances" and "speeches"')
        parser.add_argument('--work', required=True,
                            help='public_id of the Work the speeches belong to')
        parser.add_argument('--user', required=True,
                            help='admin username the change-log entries are filed under')
        parser.add_argument('--context',
                            help='context string for new instances '
                                 '(default: the Work\'s long name, "Author, Title")')
        parser.add_argument('--apply', action='store_true',
                            help='commit the changes (default: dry run, rolled back)')

    # ------------------------------------------------------------------
    def handle(self, *args, **options):
        try:
            with open(options['batch'], encoding='utf-8') as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            raise CommandError(f'cannot read {options["batch"]}: {e}')

        try:
            self.work = Work.objects.get(public_id=options['work'])
        except Work.DoesNotExist:
            raise CommandError(f'no Work with public_id {options["work"]}')
        try:
            self.user = get_user_model().objects.get(username=options['user'])
        except get_user_model().DoesNotExist:
            raise CommandError(f'no user {options["user"]!r}')
        self.context = options['context'] or self.work.get_long_name()

        errors = self.validate(data)
        if errors:
            raise CommandError('nothing written. Problems:\n  ' + '\n  '.join(errors))

        self.log = []
        try:
            with transaction.atomic():
                self.write()
                n = Speech.objects.filter(work=self.work).count()
                self.stdout.write(f'{len(self.log)} changes logged; work now has {n} speeches')
                if not options['apply']:
                    raise DryRun
        except DryRun:
            self.stdout.write(self.style.WARNING('DRY RUN: rolled back. Use --apply to commit.'))
        else:
            self.stdout.write(self.style.SUCCESS('COMMITTED.'))

    # ------------------------------------------------------------------
    def validate(self, data):
        errors = []
        for key, fields in (('instances', INSTANCE_FIELDS), ('speeches', SPEECH_FIELDS)):
            if not isinstance(data.get(key), list):
                return [f'batch has no "{key}" list']
            for i, row in enumerate(data[key], 1):
                missing = [f for f in fields if f not in row]
                if missing:
                    errors.append(f'{key} row {i}: missing {", ".join(missing)}')
        if errors:
            return errors

        self.inst_rows = {}
        for r in data['instances']:
            n = r['name']
            if n in self.inst_rows:
                errors.append(f'instance {n!r} listed twice')
            self.inst_rows[n] = r
            pid = existing_id(r['status'])
            if pid:
                if not CharacterInstance.objects.filter(public_id=pid, name=n).exists():
                    errors.append(f'instance {n!r}: no instance {pid} with that name')
                continue
            if r['status'] != 'new':
                errors.append(f'instance {n!r}: status must be "new" or "EXISTS <id>"')
            if r['char'] and not Character.objects.filter(public_id=r['char']).exists():
                errors.append(f'instance {n!r}: no Character {r["char"]}')
            for f, ok in (('being', BEING), ('number', NUMBER), ('gender', GENDER)):
                if r[f] not in ok:
                    errors.append(f'instance {n!r}: bad {f} {r[f]!r}')
            if r['anon'] not in ('yes', 'no'):
                errors.append(f'instance {n!r}: anon must be yes/no')

        self.rows = [r for r in data['speeches'] if r['status'] != 'skip']
        loci = {r['l_fi'] for r in self.rows}
        seqs = [r['seq'] for r in self.rows]
        if len(set(seqs)) != len(seqs):
            errors.append('duplicate seq values')
        for r in self.rows:
            tag = f"speech {r['l_fi']}-{r['l_la']}"
            try:
                for f in ('seq', 'cluster', 'part', 'level'):
                    int(r[f])
            except ValueError:
                errors.append(f'{tag}: seq/cluster/part/level must be integers')
                continue
            if SpeechCluster.objects.filter(seq=int(r['cluster'])) \
                    .exclude(speeches__work=self.work) \
                    .filter(speeches__isnull=False).exists():
                errors.append(f'{tag}: cluster seq {r["cluster"]} is used by another work')
            pid = existing_id(r['status'])
            if pid:
                if not Speech.objects.filter(public_id=pid, work=self.work).exists():
                    errors.append(f'{tag}: no speech {pid} in this work')
            elif r['status'] != 'new':
                errors.append(f'{tag}: status must be "new", "skip" or "EXISTS <id>"')
            if r['type'] not in TYPES:
                errors.append(f'{tag}: bad type {r["type"]!r}')
            if not names(r['spkr']):
                errors.append(f'{tag}: no speaker')
            for n in names(r['spkr']) + names(r['addr']):
                if n not in self.inst_rows:
                    errors.append(f'{tag}: {n!r} not listed under instances')
            for t in tag_list(r['tags']):
                if t not in TAGS:
                    errors.append(f'{tag}: bad tag {t!r}')
            if pid:
                continue
            if int(r['level']) > 0 and not r['embedded_in']:
                errors.append(f'{tag}: level > 0 but no embedded_in')
            if r['embedded_in'] and r['embedded_in'] not in loci and not \
                    Speech.objects.filter(work=self.work, l_fi=r['embedded_in']).exists():
                errors.append(f'{tag}: embedded_in {r["embedded_in"]} not found')
        return errors

    # ------------------------------------------------------------------
    def note(self, obj, flag, msg):
        self.log.append((obj, flag, msg))
        self.stdout.write(f'  {type(obj).__name__} {obj.public_id}: {msg}')

    def write(self):
        self.stdout.write(f'Work {self.work.public_id} {self.work}; '
                          f'new instance context {self.context!r}')

        self.stdout.write('Instances')
        self.inst = {}
        for n, r in self.inst_rows.items():
            pid = existing_id(r['status'])
            if pid:
                self.inst[n] = CharacterInstance.objects.get(public_id=pid)
                continue
            found = CharacterInstance.objects.filter(name=n, context=self.context).first()
            if found:
                self.inst[n] = found
                self.stdout.write(f'  {n}: already exists ({found.public_id})')
                continue
            i = CharacterInstance.objects.create(
                name=n, display=n, being=r['being'], number=r['number'],
                gender=r['gender'], anon=r['anon'] == 'yes', context=self.context,
                char=Character.objects.get(public_id=r['char']) if r['char'] else None)
            self.inst[n] = i
            self.note(i, ADDITION, f'created {i}')

        self.clusters = {}
        self.stdout.write('Existing speeches')
        for r in self.rows:
            pid = existing_id(r['status'])
            if pid:
                self.update_existing(Speech.objects.get(public_id=pid, work=self.work), r)

        self.stdout.write('New speeches')
        made = {}
        for r in sorted(self.rows, key=lambda r: int(r['level'])):  # parents first
            if existing_id(r['status']):
                continue
            if Speech.objects.filter(work=self.work, l_fi=r['l_fi'], l_la=r['l_la']).exists():
                self.stdout.write(f"  {r['l_fi']}-{r['l_la']}: already exists, skipped")
                continue
            parent = None
            if r['embedded_in']:
                parent = made.get(r['embedded_in']) or \
                    Speech.objects.filter(work=self.work, l_fi=r['embedded_in']).first()
            s = Speech.objects.create(
                work=self.work, cluster=self.cluster_for(r['cluster']),
                type=r['type'], seq=int(r['seq']), l_fi=r['l_fi'], l_la=r['l_la'],
                part=int(r['part']), level=int(r['level']), embedded_in=parent,
                spkr_notes=r['spkr_notes'], addr_notes=r['addr_notes'],
                notes=r['notes'])
            s.spkr.set([self.inst[n] for n in names(r['spkr'])])
            s.addr.set([self.inst[n] for n in names(r['addr'])])
            for t in tag_list(r['tags']):
                SpeechTag.objects.create(speech=s, type=t)
            made[r['l_fi']] = s
            self.note(s, ADDITION,
                      f"created {s.seq} {r['type']}{r['part']} {r['spkr']} -> {r['addr']} "
                      f"[{r['tags']}]" + (f' in {parent.l_fi}' if parent else ''))

        for obj, flag, msg in self.log:
            LogEntry.objects.log_actions(
                user_id=self.user.pk, queryset=[obj], action_flag=flag,
                change_message=f'import_speeches: {msg}', single_object=True)

    def cluster_for(self, seq):
        seq = int(seq)
        if seq not in self.clusters:
            c = SpeechCluster.objects.filter(seq=seq, speeches__work=self.work).first()
            if c is None:
                c = SpeechCluster.objects.create(seq=seq)
                self.note(c, ADDITION, f'created cluster seq {seq}')
            self.clusters[seq] = c
        return self.clusters[seq]

    def update_existing(self, s, r):
        c = s.cluster
        if c.seq != int(r['cluster']):
            old = c.seq
            c.seq = int(r['cluster'])
            c.save()
            self.note(c, CHANGE, f'seq {old} -> {c.seq}')
        self.clusters[int(r['cluster'])] = c

        changes = []
        if s.type != r['type']:
            changes.append(f'type {s.type} -> {r["type"]}')
            s.type = r['type']
            s.save()
        for field in ('spkr', 'addr'):
            want = [self.inst[n] for n in names(r[field])]
            have = list(getattr(s, field).all())
            if {i.pk for i in want} != {i.pk for i in have}:
                getattr(s, field).set(want)
                changes.append(f'{field} {"; ".join(sorted(i.name for i in have))} -> '
                               f'{"; ".join(sorted(i.name for i in want))}')
        want_tags = sorted(tag_list(r['tags']))
        have_tags = sorted(t.type for t in s.tags.all())
        if want_tags != have_tags:
            s.tags.all().delete()
            for t in want_tags:
                SpeechTag.objects.create(speech=s, type=t)
            changes.append(f'tags {", ".join(have_tags)} -> {", ".join(want_tags)}')
        if changes:
            self.note(s, CHANGE, '; '.join(changes))
