from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Deletes a user'
    
    def add_arguments(self, parser):
        parser.add_argument('user', type=str)
    
    def handle(self, *args, **options):
        try:
            user = User.objects.get(username=options['user'])
            user.delete()
            self.stderr.write(f'Deleted user {user}')
        except User.DoesNotExist:
            self.stderr.write(f'User {user} does not exist')
    