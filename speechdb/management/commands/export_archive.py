import csv
import hashlib
import subprocess
import time
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from speechdb.models import (
    Metadata, Author, Work, Character, CharacterInstance,
    SpeechCluster, Speech, SpeechTag,
)

# Bump when the layout of the exported files changes in a way an importer
# would need to know about.
FORMAT_VERSION = 1

DATASET_TITLE = 'DICES: Digital Initiative for Classics: Epic Speeches'
DATASET_URL = 'https://db.dices.mta.ca/app/'
DATASET_DOI = '10.5683/SP3/N8LS2Y'

# Listed so that every table comes after the tables it refers to, which is
# also the order an importer should load them in.
TABLES = [
    ('metadata', Metadata, 'database metadata'),
    ('authors', Author, 'authors'),
    ('works', Work, 'works'),
    ('characters', Character, 'characters'),
    ('instances', CharacterInstance, 'character instances'),
    ('clusters', SpeechCluster, 'speech clusters'),
    ('speeches', Speech, 'speeches'),
    ('tags', SpeechTag, 'speech tags'),
]

FLAT_FILE = 'speeches_flat'


def cell(value):
    '''Format one value for output: None as empty, booleans as true/false'''
    if value is None:
        return ''
    if value is True:
        return 'true'
    if value is False:
        return 'false'
    return value


def git_commit():
    '''Return the current git commit hash, or an empty string if unavailable'''
    try:
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            cwd=Path(__file__).resolve().parent,
            capture_output=True, text=True, timeout=10, check=True,
        )
    except (OSError, subprocess.SubprocessError):
        return ''
    return result.stdout.strip()


def data_filenames(ext):
    '''Files covered by the content hash, in load order. The metadata file is
    left out because it holds the hash, and so are the derived readable file
    and the README.'''
    names = []
    for name, model, _ in TABLES:
        if model is not Metadata:
            names.append(f'{name}.{ext}')
        names += [f'{model._meta.model_name}_{m2m.name}.{ext}'
                  for m2m in model._meta.many_to_many]
    return names


def content_hash(directory, ext):
    '''SHA-256 over the data files: for each file in order, its name, a NUL
    byte, its bytes, and a NUL byte.'''
    digest = hashlib.sha256()
    for filename in data_filenames(ext):
        digest.update(filename.encode('utf-8') + b'\0')
        digest.update((Path(directory) / filename).read_bytes() + b'\0')
    return digest.hexdigest()


class Command(BaseCommand):
    help = ('Export the database as delimited text files for archival '
            '(e.g. Dataverse/Borealis). The files are derived from the '
            'models, keep every id, and are meant to be importable.')

    def add_arguments(self, parser):
        parser.add_argument(
            'output_dir',
            type=str,
            help='Directory to store the exported files',
        )
        parser.add_argument(
            '--format',
            choices=['tsv', 'csv'],
            default='tsv',
            help='Delimited text format (default: tsv)',
        )
        parser.add_argument(
            '--no-readme',
            action='store_true',
            help='Skip writing README.txt',
        )
        parser.add_argument(
            '--release',
            metavar='VERSION',
            help=('Stamp this export as a release: record VERSION, the date, '
                  'the code commit and the content hash in the database '
                  'metadata. Without this option the database is not changed.'),
        )
        parser.add_argument(
            '--verify',
            action='store_true',
            help=('Treat output_dir as an existing export and check its data '
                  'files against the content hash in its metadata file'),
        )

    def handle(self, *args, **options):
        output_dir = Path(options['output_dir'])
        ext = options['format']

        if options['verify']:
            return self.verify(output_dir)

        output_dir.mkdir(parents=True, exist_ok=True)
        delimiter = '\t' if ext == 'tsv' else ','
        self.stdout.write(f'Exporting to {output_dir} ({ext.upper()})')

        written = []

        for name, model, description in TABLES:
            if model is Metadata:
                continue
            written.append(self.export_model(
                output_dir, name, model, description, ext, delimiter))
            for m2m in model._meta.many_to_many:
                written.append(self.export_junction(
                    output_dir, f'{model._meta.model_name}_{m2m.name}',
                    m2m, ext, delimiter))

        digest = content_hash(output_dir, ext)
        self.stdout.write(f'  content hash: {digest}')

        status = self.release_status(options['release'], digest)
        if options['release']:
            self.stamp_release(options['release'], digest)

        # the metadata file is written last so it includes any new stamp
        written.insert(0, self.export_model(
            output_dir, 'metadata', Metadata, 'database metadata', ext, delimiter))
        written.append(self.export_flat(output_dir, ext, delimiter))

        if not options['no_readme']:
            self.write_readme(output_dir, written, ext, digest, status)
            self.stdout.write('  README.txt')

        total = sum(count for _, _, count, _ in written)
        self.stdout.write(self.style.SUCCESS(
            f'Done: {len(written)} files, {total} rows in {output_dir}'))
        self.stdout.write(status)

    def release_status(self, release, digest):
        '''Describe how this export relates to the stamped release record'''
        if release:
            return f'This export is release {release}, stamped in the database metadata.'
        stamped = dict(Metadata.objects.values_list('name', 'value'))
        if 'content-sha256' not in stamped:
            return 'No release hash is recorded in the database metadata.'
        version = stamped.get('version', '?')
        if stamped['content-sha256'] == digest:
            return f'Identical to release {version}: no data changes since it was stamped.'
        return (f'Differs from release {version}: the data has changed since '
                f'it was stamped.')

    def stamp_release(self, version, digest):
        values = {
            'version': version,
            'date': time.strftime('%Y-%m-%d %H:%M:%S %z'),
            'git-commit': git_commit(),
            'doi': DATASET_DOI,
            'content-sha256': digest,
            'export-format': str(FORMAT_VERSION),
        }
        if not values['git-commit']:
            del values['git-commit']
        with transaction.atomic():
            for name, value in values.items():
                Metadata.objects.update_or_create(name=name, defaults={'value': value})

    def verify(self, directory):
        for ext in ('tsv', 'csv'):
            if (directory / f'authors.{ext}').exists():
                break
        else:
            raise CommandError(f'No export files found in {directory}')

        missing = [n for n in data_filenames(ext) if not (directory / n).exists()]
        if missing:
            raise CommandError(f'Missing files: {", ".join(missing)}')

        delimiter = '\t' if ext == 'tsv' else ','
        meta_path = directory / f'metadata.{ext}'
        if not meta_path.exists():
            raise CommandError(f'Missing {meta_path.name}')
        with open(meta_path, newline='', encoding='utf-8') as f:
            records = {r['name']: r['value']
                       for r in csv.DictReader(f, delimiter=delimiter)}
        recorded = records.get('content-sha256')
        if not recorded:
            raise CommandError(f'{meta_path.name} has no content-sha256 record')

        actual = content_hash(directory, ext)
        if actual != recorded:
            raise CommandError(
                f'Content hash mismatch: files give {actual}, metadata records {recorded}')
        self.stdout.write(self.style.SUCCESS(
            f'OK: files match release {records.get("version", "?")} ({actual})'))

    def write_rows(self, path, header, rows, delimiter):
        count = 0
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=delimiter, lineterminator='\n')
            writer.writerow(header)
            for row in rows:
                writer.writerow([cell(v) for v in row])
                count += 1
        self.stdout.write(f'  {path.name}: {count} rows')
        return count

    def export_model(self, output_dir, name, model, description, ext, delimiter):
        '''One file per model, one column per concrete field (foreign keys
        as <field>_id), so new model fields are exported automatically.'''
        header = [f.attname for f in model._meta.concrete_fields]
        rows = model.objects.order_by('pk').values_list(*header)
        filename = f'{name}.{ext}'
        count = self.write_rows(output_dir / filename, header, rows, delimiter)
        return (filename, header, count, description)

    def export_junction(self, output_dir, name, m2m, ext, delimiter):
        '''One file per many-to-many relation, one row per link'''
        through = m2m.remote_field.through
        fields = [f for f in through._meta.concrete_fields
                  if not (through._meta.auto_created and f.primary_key)]
        header = [f.attname for f in fields]
        rows = through.objects.order_by('pk').values_list(*header)
        filename = f'{name}.{ext}'
        count = self.write_rows(output_dir / filename, header, rows, delimiter)
        return (filename, header, count, f'links: {m2m.model._meta.model_name}.{m2m.name}')

    def export_flat(self, output_dir, ext, delimiter):
        '''A readable one-row-per-speech file for people. Importers ignore it.'''
        header = [
            'public_id', 'author', 'work', 'from', 'to', 'cluster', 'cluster_seq',
            'type', 'part', 'level', 'embedded_in', 'speakers', 'addressees',
            'speaker_notes', 'addressee_notes', 'tags', 'notes',
        ]
        speeches = (Speech.objects
                    .select_related('work__author', 'cluster', 'embedded_in')
                    .prefetch_related('spkr', 'addr', 'tags')
                    .order_by('cluster__seq', 'seq', 'pk'))

        def rows():
            for s in speeches:
                tags = sorted(f'{t.type}?' if t.doubt else t.type for t in s.tags.all())
                yield [
                    s.public_id, s.work.author.name, s.work.title, s.l_fi, s.l_la,
                    s.cluster.public_id, s.cluster.seq, s.type, s.part, s.level,
                    s.embedded_in.public_id if s.embedded_in else '',
                    '; '.join(i.name for i in s.spkr.all()),
                    '; '.join(i.name for i in s.addr.all()),
                    s.spkr_notes, s.addr_notes, ';'.join(tags), s.notes,
                ]

        filename = f'{FLAT_FILE}.{ext}'
        count = self.write_rows(output_dir / filename, header, rows(), delimiter)
        return (filename, header, count, 'readable summary, derived; ignored on import')

    def write_readme(self, output_dir, written, ext, digest, status):
        stamped = dict(Metadata.objects.values_list('name', 'value'))
        commit = git_commit()

        lines = [
            DATASET_TITLE,
            '=' * len(DATASET_TITLE),
            '',
            f'Export date:     {time.strftime("%Y-%m-%d %H:%M:%S %z")}',
            f'Export format:   version {FORMAT_VERSION}',
        ]
        if stamped.get('version'):
            lines.append(f'Release:         {stamped["version"]} ({stamped.get("date", "")})')
        if commit:
            lines.append(f'Git commit:      {commit}')
        lines += [
            f'Content hash:    {digest}',
            f'Status:          {status}',
            '',
            'Format',
            '------',
            f'  {ext.upper()} files, UTF-8, first row is the header, "\\n" line endings.',
            '  Fields containing the delimiter, quotes or line breaks are quoted.',
            '  Booleans are true/false. A missing value (e.g. an unlinked',
            '  character or no embedding speech) is an empty field.',
            '  Every file keeps the database ids: <name>_id columns refer to the',
            '  id column of the related file, and public_id is the stable public',
            '  identifier used in DICES URNs.',
            '',
            'Verifying',
            '---------',
            '  content-sha256 in metadata is the SHA-256 of the data files: for',
            '  each file in the order listed under Files (skipping metadata and',
            '  speeches_flat), its name, a NUL byte, its bytes, and a NUL byte.',
            '  With the DICES code: python manage.py export_archive <dir> --verify',
            '',
            'Files',
            '-----',
            '  Load the model files in the order below: each refers only to files',
            '  listed before it, except speeches.embedded_in_id, which refers to',
            '  another row of speeches (load it in a second pass).',
            '',
        ]
        for filename, header, count, description in written:
            lines.append(f'  {filename}  ({count} rows)  {description}')
            lines.append(f'      columns: {", ".join(header)}')
        lines += [
            '',
            'Citation',
            '--------',
            f'  {DATASET_TITLE}',
            f'  {DATASET_URL}',
            f'  DOI: {DATASET_DOI}',
            f'  https://borealisdata.ca/dataset.xhtml?persistentId=doi:{DATASET_DOI}',
            '',
        ]
        (output_dir / 'README.txt').write_text('\n'.join(lines), encoding='utf-8')
