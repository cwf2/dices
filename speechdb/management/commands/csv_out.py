import csv
import os
from django.core.management.base import BaseCommand
from django.apps import apps

class Command(BaseCommand):
    help = 'Export tables as CSV for archive'
    
    def add_arguments(self, parser):
        parser.add_argument('path', type=str)
    
    def handle(self, *args, **options):
        path = options['path']
        
        for model in apps.get_models():
            filename = f"{model._meta.model_name}.csv"
            with open(os.path.join(path, filename), "w", newline="") as f:
                writer = csv.writer(f)
                fields = [field.name for field in model._meta.fields]
                writer.writerow(fields)
                for obj in model.objects.values_list(*fields):
                    writer.writerow(obj)