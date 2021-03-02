# Generated by Django 3.0.7 on 2021-02-25 13:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('speechdb', '0010_auto_20200624_1456'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='author',
            options={'ordering': ['name']},
        ),
        migrations.AlterModelOptions(
            name='character',
            options={'ordering': ['name']},
        ),
        migrations.AlterModelOptions(
            name='characterinstance',
            options={'ordering': ['char']},
        ),
        migrations.AlterModelOptions(
            name='speech',
            options={'ordering': ['cluster__work', 'seq']},
        ),
        migrations.AlterModelOptions(
            name='speechcluster',
            options={'ordering': ['work', 'speech']},
        ),
        migrations.AlterModelOptions(
            name='work',
            options={'ordering': ['author', 'title']},
        ),
        migrations.AlterField(
            model_name='character',
            name='wd',
            field=models.CharField(blank=True, max_length=32, verbose_name='WikiData ID'),
        ),
    ]
