# Generated by Django 3.0.7 on 2021-03-02 11:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('speechdb', '0014_auto_20210225_1324'),
    ]

    operations = [
        migrations.AlterField(
            model_name='speechcluster',
            name='type',
            field=models.CharField(choices=[('S', 'Soliloquy'), ('M', 'Monologue'), ('D', 'Dialogue'), ('G', 'General')], max_length=1),
        ),
    ]
