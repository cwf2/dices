# Generated by Django 3.1.8 on 2021-05-27 14:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('speechdb', '0011_auto_20210510_1957'),
    ]

    operations = [
        migrations.RenameField(
            model_name='character',
            old_name='type',
            new_name='number',
        ),
    ]
