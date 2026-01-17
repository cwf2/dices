import os
import subprocess
import time
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from git import Repo, InvalidGitRepositoryError


class Command(BaseCommand):
    help = 'Create versioned database backups with PostgreSQL dumps and Django JSON fixtures'

    def add_arguments(self, parser):
        parser.add_argument(
            '--backup-dir',
            type=str,
            default='backups',
            help='Directory to store backups (default: backups/)'
        )
        parser.add_argument(
            '--format',
            choices=['pg_dump', 'json', 'both'],
            default='both',
            help='Backup format: pg_dump (PostgreSQL), json (Django fixture), or both'
        )
        parser.add_argument(
            '--git-commit',
            action='store_true',
            help='Automatically commit backup to git'
        )
        parser.add_argument(
            '--keep-last',
            type=int,
            help='Keep only N most recent backups (auto-cleanup)'
        )

    def handle(self, *args, **options):
        backup_dir = Path(options['backup_dir'])
        backup_dir.mkdir(exist_ok=True)

        timestamp = time.strftime('%Y-%m-%d_%H-%M-%S')

        # Get database configuration
        db_config = settings.DATABASES['default']
        db_engine = db_config['ENGINE']

        backups_created = []

        # PostgreSQL dump
        if options['format'] in ['pg_dump', 'both']:
            if 'postgresql' not in db_engine:
                self.stderr.write(
                    self.style.WARNING(
                        f"pg_dump format requires PostgreSQL, but using {db_engine}. Skipping."
                    )
                )
            else:
                pg_backup_file = backup_dir / f"dices_db_{timestamp}.sql"
                self.stdout.write(f"Creating PostgreSQL dump: {pg_backup_file}")

                try:
                    # Build pg_dump command
                    env = os.environ.copy()
                    if db_config.get('PASSWORD'):
                        env['PGPASSWORD'] = db_config['PASSWORD']

                    cmd = ['pg_dump']
                    if db_config.get('HOST'):
                        cmd.extend(['-h', db_config['HOST']])
                    if db_config.get('PORT'):
                        cmd.extend(['-p', str(db_config['PORT'])])
                    if db_config.get('USER'):
                        cmd.extend(['-U', db_config['USER']])
                    cmd.extend([
                        '-Fp',  # Plain text format
                        '--no-owner',  # Don't include ownership commands
                        '--no-acl',  # Don't include ACL commands
                        '-f', str(pg_backup_file),
                        db_config['NAME']
                    ])

                    subprocess.run(cmd, env=env, check=True, capture_output=True)
                    backups_created.append(pg_backup_file)

                    # Create compressed version
                    subprocess.run(['gzip', '-k', str(pg_backup_file)], check=True)
                    backups_created.append(Path(str(pg_backup_file) + '.gz'))

                    self.stdout.write(
                        self.style.SUCCESS(f"✓ PostgreSQL dump created: {pg_backup_file}.gz")
                    )

                except subprocess.CalledProcessError as e:
                    raise CommandError(f"pg_dump failed: {e.stderr.decode() if e.stderr else str(e)}")

        # Django JSON fixture
        if options['format'] in ['json', 'both']:
            json_backup_file = backup_dir / f"dices_fixture_{timestamp}.json"
            self.stdout.write(f"Creating Django JSON fixture: {json_backup_file}")

            try:
                # Use Django's dumpdata command
                from django.core.management import call_command
                with open(json_backup_file, 'w') as f:
                    call_command('dumpdata', 'speechdb', stdout=f, indent=2)

                backups_created.append(json_backup_file)

                # Create compressed version
                subprocess.run(['gzip', '-k', str(json_backup_file)], check=True)
                backups_created.append(Path(str(json_backup_file) + '.gz'))

                self.stdout.write(
                    self.style.SUCCESS(f"✓ JSON fixture created: {json_backup_file}.gz")
                )

            except Exception as e:
                raise CommandError(f"JSON fixture creation failed: {str(e)}")

        # Git commit if requested
        if options['git_commit']:
            try:
                repo = Repo(search_parent_directories=True)

                # Add backup files
                for backup_file in backups_created:
                    repo.index.add([str(backup_file)])

                # Commit
                commit_msg = f"Database backup {timestamp}"
                repo.index.commit(commit_msg)

                self.stdout.write(
                    self.style.SUCCESS(f"✓ Backup committed to git: {commit_msg}")
                )

            except InvalidGitRepositoryError:
                self.stderr.write(
                    self.style.WARNING("Not in a git repository, skipping git commit")
                )
            except Exception as e:
                self.stderr.write(
                    self.style.WARNING(f"Git commit failed: {str(e)}")
                )

        # Cleanup old backups if requested
        if options['keep_last']:
            self._cleanup_old_backups(backup_dir, options['keep_last'])

        self.stdout.write(
            self.style.SUCCESS(f"\n✓ Backup complete! {len(backups_created)} files created.")
        )

    def _cleanup_old_backups(self, backup_dir, keep_count):
        """Remove old backup files, keeping only the N most recent"""

        # Get all backup files sorted by modification time
        all_backups = sorted(
            backup_dir.glob('dices_*'),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        # Remove old files
        removed_count = 0
        for old_backup in all_backups[keep_count:]:
            old_backup.unlink()
            removed_count += 1
            self.stdout.write(f"Removed old backup: {old_backup.name}")

        if removed_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f"✓ Cleaned up {removed_count} old backup(s)")
            )
