# Generated by Django 3.0.7 on 2020-06-13 12:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Author',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64)),
                ('wd', models.CharField(max_length=32, verbose_name='WikiData ID')),
            ],
        ),
        migrations.CreateModel(
            name='Character',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64)),
                ('wd', models.CharField(max_length=32, verbose_name='WikiData ID')),
                ('manto', models.CharField(max_length=32, verbose_name='MANTO ID')),
            ],
        ),
        migrations.CreateModel(
            name='CharacterInstance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('char', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='instances', to='speechdb.Character')),
                ('disg', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='disguises', to='speechdb.Character')),
            ],
        ),
        migrations.CreateModel(
            name='Work',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=64)),
                ('urn', models.CharField(max_length=128)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='speechdb.Author')),
            ],
        ),
        migrations.CreateModel(
            name='SpeechCluster',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('S', 'Soliloqy'), ('M', 'Monologue'), ('D', 'Dialogue'), ('G', 'General')], max_length=1)),
                ('work', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='speechdb.Work')),
            ],
        ),
        migrations.CreateModel(
            name='Speech',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('l_fi', models.CharField(max_length=8, verbose_name='first line')),
                ('l_la', models.CharField(max_length=8, verbose_name='last line')),
                ('addr', models.ManyToManyField(related_name='addresses', to='speechdb.CharacterInstance')),
                ('cluster', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='speechdb.SpeechCluster')),
                ('spkr', models.ManyToManyField(related_name='speeches', to='speechdb.CharacterInstance')),
            ],
        ),
    ]
