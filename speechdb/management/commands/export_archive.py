import csv
import os
import time
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db.models import Count
from git import Repo, InvalidGitRepositoryError

from speechdb.models import (
    Author, Work, Character, CharacterInstance,
    Speech, SpeechCluster, SpeechTag, Metadata
)


class Command(BaseCommand):
    help = 'Export database to CSV files for archival (e.g., Dataverse/Borealis)'

    def add_arguments(self, parser):
        parser.add_argument(
            'output_dir',
            type=str,
            help='Directory to store CSV exports'
        )
        parser.add_argument(
            '--delimiter',
            type=str,
            default='\t',
            choices=[',', '\t', '|'],
            help='CSV delimiter (default: tab)'
        )
        parser.add_argument(
            '--create-readme',
            action='store_true',
            help='Create README.txt with export metadata'
        )

    def handle(self, *args, **options):
        output_dir = Path(options['output_dir'])
        output_dir.mkdir(parents=True, exist_ok=True)

        delimiter = options['delimiter']
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S %z')

        self.stdout.write(f"Exporting to: {output_dir}")
        self.stdout.write(f"Delimiter: {'TAB' if delimiter == '\\t' else delimiter}\n")

        # Export each model
        export_count = 0

        # Authors
        authors_file = output_dir / 'authors.tsv'
        self.stdout.write(f"Exporting authors to {authors_file.name}...")
        with open(authors_file, 'w', newline='') as f:
            writer = csv.writer(f, delimiter=delimiter)
            writer.writerow(['id', 'name', 'wd', 'urn'])

            for author in Author.objects.all().order_by('id'):
                writer.writerow([
                    author.id,
                    author.name,
                    author.wd or '',
                    author.urn or '',
                ])
                export_count += 1

        self.stdout.write(self.style.SUCCESS(f"  ✓ {Author.objects.count()} authors"))

        # Works
        works_file = output_dir / 'works.tsv'
        self.stdout.write(f"Exporting works to {works_file.name}...")
        with open(works_file, 'w', newline='') as f:
            writer = csv.writer(f, delimiter=delimiter)
            writer.writerow(['id', 'author', 'title', 'lang', 'wd', 'urn', 'tlg'])

            for work in Work.objects.all().order_by('id'):
                writer.writerow([
                    work.id,
                    work.author.id,
                    work.title,
                    work.lang,
                    work.wd or '',
                    work.urn or '',
                    work.tlg or '',
                ])
                export_count += 1

        self.stdout.write(self.style.SUCCESS(f"  ✓ {Work.objects.count()} works"))

        # Characters
        chars_file = output_dir / 'characters.tsv'
        self.stdout.write(f"Exporting characters to {chars_file.name}...")
        with open(chars_file, 'w', newline='') as f:
            writer = csv.writer(f, delimiter=delimiter)
            writer.writerow(['name', 'being', 'number', 'gender', 'wd', 'manto', 'topostext', 'notes'])

            for char in Character.objects.all().order_by('name'):
                writer.writerow([
                    char.name,
                    char.being,
                    char.number,
                    char.gender,
                    char.wd or '',
                    char.manto or '',
                    char.tt or '',
                    char.notes or '',
                ])
                export_count += 1

        self.stdout.write(self.style.SUCCESS(f"  ✓ {Character.objects.count()} characters"))

        # Character Instances
        instances_file = output_dir / 'instances.tsv'
        self.stdout.write(f"Exporting character instances to {instances_file.name}...")
        with open(instances_file, 'w', newline='') as f:
            writer = csv.writer(f, delimiter=delimiter)
            writer.writerow([
                'name', 'instance of', 'screen name', 'being', 'number', 'gender',
                'disguise', 'context', 'anon', 'notes'
            ])

            for inst in CharacterInstance.objects.all().order_by('name', 'context'):
                writer.writerow([
                    inst.name,
                    inst.char.name if inst.char else '',
                    inst.display,
                    inst.being,
                    inst.number,
                    inst.gender,
                    inst.disguise or '',
                    inst.context,
                    'yes' if inst.anon else 'no',
                    inst.notes or '',
                ])
                export_count += 1

        self.stdout.write(self.style.SUCCESS(f"  ✓ {CharacterInstance.objects.count()} instances"))

        # Speeches (main data - may be multiple files if very large)
        speeches_file = output_dir / 'speeches.tsv'
        self.stdout.write(f"Exporting speeches to {speeches_file.name}...")
        with open(speeches_file, 'w', newline='') as f:
            writer = csv.writer(f, delimiter=delimiter)
            writer.writerow([
                'seq', 'work_id', 'from_book', 'from_line', 'to_book', 'to_line',
                'cluster_id', 'cluster_part', 'turn_type', 'embedded_level',
                'speaker', 'addressee', 'speaker_notes', 'addressee_notes',
                'misc_notes', 'short_speech_type'
            ])

            for speech in Speech.objects.all().order_by('seq'):
                # Parse book.line format
                l_fi_parts = speech.l_fi.split('.')
                from_book = l_fi_parts[0] if len(l_fi_parts) > 1 else ''
                from_line = l_fi_parts[-1]

                l_la_parts = speech.l_la.split('.')
                to_book = l_la_parts[0] if len(l_la_parts) > 1 else ''
                to_line = l_la_parts[-1]

                # Get speakers and addressees
                speakers = ';'.join(s.name for s in speech.spkr.all())
                addressees = ';'.join(a.name for a in speech.addr.all())

                # Get tags
                tags = SpeechTag.objects.filter(speech=speech)
                tag_str = ';'.join(
                    f"{tag.type}?" if tag.doubt else tag.type
                    for tag in tags
                )

                writer.writerow([
                    speech.seq,
                    speech.work.id,
                    from_book,
                    from_line,
                    to_book,
                    to_line,
                    speech.cluster.id,
                    speech.part,
                    speech.type,
                    speech.level,
                    speakers,
                    addressees,
                    speech.spkr_notes or '',
                    speech.addr_notes or '',
                    speech.notes or '',
                    tag_str,
                ])
                export_count += 1

        self.stdout.write(self.style.SUCCESS(f"  ✓ {Speech.objects.count()} speeches"))

        # Speech Clusters
        clusters_file = output_dir / 'clusters.tsv'
        self.stdout.write(f"Exporting speech clusters to {clusters_file.name}...")
        with open(clusters_file, 'w', newline='') as f:
            writer = csv.writer(f, delimiter=delimiter)
            writer.writerow(['id', 'public_id', 'seq', 'speech_count'])

            for cluster in SpeechCluster.objects.all().order_by('seq'):
                speech_count = Speech.objects.filter(cluster=cluster).count()
                writer.writerow([
                    cluster.id,
                    cluster.public_id,
                    cluster.seq,
                    speech_count,
                ])

        self.stdout.write(self.style.SUCCESS(f"  ✓ {SpeechCluster.objects.count()} clusters"))

        # Speech Tags
        tags_file = output_dir / 'tags.tsv'
        self.stdout.write(f"Exporting speech tags to {tags_file.name}...")
        with open(tags_file, 'w', newline='') as f:
            writer = csv.writer(f, delimiter=delimiter)
            writer.writerow(['id', 'speech_seq', 'type', 'doubt'])

            for tag in SpeechTag.objects.all().order_by('speech__seq', 'type'):
                writer.writerow([
                    tag.id,
                    tag.speech.seq,
                    tag.type,
                    'yes' if tag.doubt else 'no',
                ])

        self.stdout.write(self.style.SUCCESS(f"  ✓ {SpeechTag.objects.count()} tags"))

        # Create README if requested
        if options['create_readme']:
            self._create_readme(output_dir, timestamp)

        self.stdout.write(
            self.style.SUCCESS(f"\n✓ Export complete! {export_count} total records exported to {output_dir}")
        )

    def _create_readme(self, output_dir, timestamp):
        """Create README.txt with export metadata"""

        readme_file = output_dir / 'README.txt'

        # Get git info if available
        git_commit = ''
        try:
            repo = Repo(search_parent_directories=True)
            git_commit = repo.head.object.hexsha
        except (InvalidGitRepositoryError, Exception):
            pass

        # Get database metadata if available
        db_version = ''
        try:
            version_meta = Metadata.objects.filter(name='version').first()
            if version_meta:
                db_version = version_meta.value
        except Exception:
            pass

        with open(readme_file, 'w') as f:
            f.write("DICES Database Export\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"Export Date: {timestamp}\n")
            if db_version:
                f.write(f"Database Version: {db_version}\n")
            if git_commit:
                f.write(f"Git Commit: {git_commit}\n")
            f.write("\n")

            f.write("Files:\n")
            f.write("-" * 70 + "\n")
            f.write("  authors.tsv          - Authors (Homer, Vergil, etc.)\n")
            f.write("  works.tsv            - Literary works (Iliad, Aeneid, etc.)\n")
            f.write("  characters.tsv       - Character definitions\n")
            f.write("  instances.tsv        - Character instances in specific contexts\n")
            f.write("  speeches.tsv         - Direct speech data (main dataset)\n")
            f.write("  clusters.tsv         - Speech cluster metadata\n")
            f.write("  tags.tsv             - Speech type tags\n")
            f.write("\n")

            f.write("Format:\n")
            f.write("-" * 70 + "\n")
            f.write("  All files use tab-separated values (TSV)\n")
            f.write("  First row contains column headers\n")
            f.write("  Empty fields are represented as empty strings\n")
            f.write("\n")

            f.write("Statistics:\n")
            f.write("-" * 70 + "\n")
            f.write(f"  Authors:              {Author.objects.count():>6}\n")
            f.write(f"  Works:                {Work.objects.count():>6}\n")
            f.write(f"  Characters:           {Character.objects.count():>6}\n")
            f.write(f"  Character Instances:  {CharacterInstance.objects.count():>6}\n")
            f.write(f"  Speeches:             {Speech.objects.count():>6}\n")
            f.write(f"  Speech Clusters:      {SpeechCluster.objects.count():>6}\n")
            f.write(f"  Speech Tags:          {SpeechTag.objects.count():>6}\n")
            f.write("\n")

            f.write("Citation:\n")
            f.write("-" * 70 + "\n")
            f.write("  DICES: Database of Information on Creatures and Episodes in Speech\n")
            f.write("  https://www.epicspeeches.net\n")
            f.write("  DOI: 10.5683/SP3/N8LS2Y\n")
            f.write("  https://borealisdata.ca/dataset.xhtml?persistentId=doi:10.5683/SP3/N8LS2Y\n")

        self.stdout.write(self.style.SUCCESS(f"  ✓ README created: {readme_file.name}"))
