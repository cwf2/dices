from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Creates a user for web authentication'
    
    def add_arguments(self, parser):
        parser.add_argument('user', type=str)
        parser.add_argument('password', type=str)
    
    def handle(self, *args, **options):
        user = User.objects.create_user(options['user'], password=options['password'])
        user.save()
        self.stderr.write(f'Created user {user}')
