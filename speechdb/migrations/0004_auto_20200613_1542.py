# Generated by Django 3.0.7 on 2020-06-13 18:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('speechdb', '0003_character_being'),
    ]

    operations = [
        migrations.AlterField(
            model_name='character',
            name='manto',
            field=models.CharField(max_length=32, unique=True, verbose_name='MANTO ID'),
        ),
        migrations.AlterField(
            model_name='character',
            name='wd',
            field=models.CharField(max_length=32, unique=True, verbose_name='WikiData ID'),
        ),
    ]
