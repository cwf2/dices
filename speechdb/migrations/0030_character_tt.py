# Generated by Django 3.1.8 on 2023-06-27 14:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('speechdb', '0029_auto_20230503_2028'),
    ]

    operations = [
        migrations.AddField(
            model_name='character',
            name='tt',
            field=models.CharField(max_length=32, null=True, verbose_name='ToposText ID'),
        ),
    ]
