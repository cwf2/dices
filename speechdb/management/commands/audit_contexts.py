'''Check every CharacterInstance.context against the work it is used in.

    python manage.py audit_contexts                       # report only
    python manage.py audit_contexts --apply --user chris  # fix mismatches

An instance's context should be its work's get_context_name(), "Author
Title" (no comma), where "its work" is the work of the speeches it speaks
or is addressed in. Reported:

  mismatch    context differs from the expected string (fixed by --apply)
  multi-work  instance used in speeches of more than one work (not fixed:
              needs a human decision, usually splitting the instance)
  orphan      instance used by no speech (not fixed)

Run it after renaming a Work or an Author: their instances keep the old
name in `context` until this is applied. With --apply every change is
recorded in the admin history under --user, prefixed "audit_contexts:".
'''
from collections import defaultdict

from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from speechdb.models import CharacterInstance, Speech, Work


class Command(BaseCommand):
    help = 'Report (and with --apply, fix) CharacterInstance.context values that do not match their work'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true',
                            help='rewrite mismatched contexts (default: report only)')
        parser.add_argument('--user',
                            help='admin username for the change-log entries (required with --apply)')

    def handle(self, *args, **options):
        user = None
        if options['apply']:
            if not options['user']:
                raise CommandError('--apply needs --user')
            try:
                user = get_user_model().objects.get(username=options['user'])
            except get_user_model().DoesNotExist:
                raise CommandError(f'no user {options["user"]!r}')

        works_of = defaultdict(set)
        for rel in (Speech.spkr.through, Speech.addr.through):
            for inst_id, work_id in rel.objects.values_list(
                    'characterinstance_id', 'speech__work_id'):
                works_of[inst_id].add(work_id)
        works = {w.pk: w for w in Work.objects.select_related('author')}

        mismatch, multi, orphan = [], [], []
        for inst in CharacterInstance.objects.order_by('context', 'name', 'id'):
            ws = works_of.get(inst.pk, set())
            if not ws:
                orphan.append(inst)
            elif len(ws) > 1:
                multi.append((inst, sorted(works[w].get_context_name() for w in ws)))
            else:
                expected = works[next(iter(ws))].get_context_name()
                if inst.context != expected:
                    mismatch.append((inst, expected))

        total = CharacterInstance.objects.count()
        self.stdout.write(f'{total} instances: {total - len(mismatch) - len(multi) - len(orphan)} ok, '
                          f'{len(mismatch)} mismatch, {len(multi)} multi-work, {len(orphan)} orphan')
        for inst, expected in mismatch:
            self.stdout.write(f'  mismatch   {inst.public_id} {inst.name}: '
                              f'{inst.context!r} -> {expected!r}')
        for inst, names in multi:
            self.stdout.write(f'  multi-work {inst.public_id} {inst.name} ({inst.context}): '
                              + '; '.join(names))
        for inst in orphan:
            self.stdout.write(f'  orphan     {inst.public_id} {inst.name} ({inst.context})')

        if not options['apply'] or not mismatch:
            return
        with transaction.atomic():
            for inst, expected in mismatch:
                old = inst.context
                inst.context = expected
                inst.save(update_fields=['context'])
                LogEntry.objects.log_actions(
                    user_id=user.pk, queryset=[inst], action_flag=CHANGE,
                    change_message=f'audit_contexts: context {old!r} -> {expected!r}',
                    single_object=True)
        self.stdout.write(self.style.SUCCESS(f'fixed {len(mismatch)} contexts'))
