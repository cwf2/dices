# Generated by Django 3.1.8 on 2021-08-28 15:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('speechdb', '0019_work_lang'),
    ]

    operations = [
        migrations.CreateModel(
            name='Metadata',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64, unique=True)),
                ('value', models.TextField()),
            ],
        ),
    ]
