# Generated by Django 3.1.8 on 2021-06-18 16:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('speechdb', '0015_auto_20210616_1542'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='characterinstance',
            options={'ordering': ['name']},
        ),
        migrations.AlterField(
            model_name='character',
            name='gender',
            field=models.CharField(choices=[('none', 'Unknown/not-applicable'), ('non-binary', 'Mixed/non-binary'), ('female', 'Female'), ('male', 'Male')], default='none', max_length=16),
        ),
        migrations.AlterField(
            model_name='characterinstance',
            name='being',
            field=models.CharField(choices=[('mortal', 'Mortal'), ('divine', 'Divine'), ('creature', 'Mythical Creature'), ('other', 'Other')], default='mortal', max_length=16),
        ),
        migrations.AlterField(
            model_name='characterinstance',
            name='char',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='instances', to='speechdb.character'),
        ),
        migrations.AlterField(
            model_name='characterinstance',
            name='disg',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='disguises', to='speechdb.character'),
        ),
        migrations.AlterField(
            model_name='characterinstance',
            name='gender',
            field=models.CharField(choices=[('none', 'Unknown/not-applicable'), ('non-binary', 'Mixed/non-binary'), ('female', 'Female'), ('male', 'Male')], default='none', max_length=16),
        ),
        migrations.AlterField(
            model_name='characterinstance',
            name='name',
            field=models.CharField(default='', max_length=64),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='characterinstance',
            name='number',
            field=models.CharField(choices=[('individual', 'Individual'), ('collective', 'Collective'), ('other', 'Other')], default='individual', max_length=16),
        ),
    ]