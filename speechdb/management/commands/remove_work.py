'''Remove a Work and everything that exists only for it.

    python manage.py remove_work 4E92 --user chris            # dry run
    python manage.py remove_work 4E92 --user chris --apply

For scope decisions (a poem judged out of scope for DICES). Deletes, in a
single transaction:

  - every Speech of the work (their SpeechTags go with them)
  - SpeechClusters left empty by that
  - CharacterInstances used by those speeches and by nothing else
  - the Work itself

Characters and the Author are never touched. Refuses to run if a speech
in another work is embedded in one of these speeches.

Each deleted object gets an admin-history (LogEntry) DELETION entry under
--user whose message holds the object's full serialized data (speeches
also list speakers, addressees and tags by name), so the record can be
recovered or the decision revisited. Without --apply everything is rolled
back.
'''
import json

from django.contrib.admin.models import DELETION, LogEntry
from django.contrib.auth import get_user_model
from django.core import serializers
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from speechdb.models import CharacterInstance, Speech, SpeechCluster, Work


class DryRun(Exception):
    pass


def snapshot(obj, **extra):
    data = json.loads(serializers.serialize('json', [obj]))[0]
    data.update(extra)
    return json.dumps(data, ensure_ascii=False, sort_keys=True)


class Command(BaseCommand):
    help = 'Remove a Work with its speeches, emptied clusters and its own instances (dry run unless --apply)'

    def add_arguments(self, parser):
        parser.add_argument('work', help='public_id of the Work')
        parser.add_argument('--user', required=True,
                            help='admin username for the change-log entries')
        parser.add_argument('--reason', default='',
                            help='short reason, recorded in each log entry')
        parser.add_argument('--apply', action='store_true',
                            help='commit (default: dry run, rolled back)')

    def handle(self, *args, **options):
        try:
            work = Work.objects.select_related('author').get(public_id=options['work'])
        except Work.DoesNotExist:
            raise CommandError(f'no Work with public_id {options["work"]}')
        try:
            user = get_user_model().objects.get(username=options['user'])
        except get_user_model().DoesNotExist:
            raise CommandError(f'no user {options["user"]!r}')
        prefix = 'remove_work' + (f' ({options["reason"]})' if options['reason'] else '') + ': '

        speeches = list(Speech.objects.filter(work=work)
                        .select_related('cluster').prefetch_related('spkr', 'addr', 'tags'))
        outside = Speech.objects.filter(embedded_in__in=speeches).exclude(work=work)
        if outside.exists():
            raise CommandError('speeches in other works are embedded in this one: '
                               + ', '.join(s.public_id for s in outside))

        insts = set()
        for s in speeches:
            insts.update(s.spkr.all())
            insts.update(s.addr.all())
        clusters = {s.cluster for s in speeches}

        log = []

        def note(obj, text):
            log.append((obj, text))
            self.stdout.write(f'  delete {type(obj).__name__} {obj.public_id}: {obj}')

        try:
            with transaction.atomic():
                self.stdout.write(f'Work {work.public_id} {work}: {len(speeches)} speeches')
                ids = [s.pk for s in speeches]
                for s in speeches:
                    note(s, snapshot(s, spkr=[str(i) for i in s.spkr.all()],
                                     addr=[str(i) for i in s.addr.all()],
                                     tags=[t.type for t in s.tags.all()]))
                for obj, text in log:
                    LogEntry.objects.log_actions(
                        user_id=user.pk, queryset=[obj], action_flag=DELETION,
                        change_message=prefix + text, single_object=True)
                log.clear()
                Speech.objects.filter(pk__in=ids).update(embedded_in=None)
                Speech.objects.filter(pk__in=ids).delete()

                for c in sorted(clusters, key=lambda c: c.seq):
                    if not c.speeches.exists():
                        note(c, snapshot(c))
                for i in sorted(insts, key=lambda i: i.name):
                    if not (i.speeches.exists() or i.addresses.exists()):
                        note(i, snapshot(i))
                    else:
                        self.stdout.write(f'  keep   CharacterInstance {i.public_id} {i}: used elsewhere')
                note(work, snapshot(work))

                for obj, text in log:
                    LogEntry.objects.log_actions(
                        user_id=user.pk, queryset=[obj], action_flag=DELETION,
                        change_message=prefix + text, single_object=True)
                    obj.delete()

                self.stdout.write(f'{len(ids) + len(log)} objects removed')
                if not options['apply']:
                    raise DryRun
        except DryRun:
            self.stdout.write(self.style.WARNING('DRY RUN: rolled back. Use --apply to commit.'))
        else:
            self.stdout.write(self.style.SUCCESS('COMMITTED.'))
