# Generated by Django 3.1.8 on 2022-12-07 13:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('speechdb', '0026_auto_20221207_0814'),
    ]

    operations = [
        migrations.AlterField(
            model_name='speechtag',
            name='type',
            field=models.CharField(choices=[('cha', 'Challenge'), ('com', 'Command'), ('con', 'Consolation'), ('del', 'Deliberation'), ('des', 'Desire and Wish'), ('exh', 'Exhortation and Self-Exhortation'), ('far', 'Farewell'), ('gre', 'Greeting and Reception'), ('inf', 'Information and Description'), ('inv', 'Invitation'), ('ins', 'Instruction'), ('lam', 'Lament'), ('lau', 'Praise and Laudation'), ('mes', 'Message'), ('nar', 'Narration'), ('ora', 'Prophecy, Oracular Speech, and Interpretation'), ('per', 'Persuasion'), ('pra', 'Prayer'), ('que', 'Question'), ('req', 'Request'), ('res', 'Reply to Question'), ('tau', 'Taunt'), ('thr', 'Threat'), ('vit', 'Vituperation'), ('vow', 'Promise and Oath'), ('war', 'Warning'), ('und', 'Undefined')], default='und', max_length=3),
        ),
    ]
