# Generated by Django 2.1.5 on 2019-01-04 18:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inia', '0002_remove_iniagene_publication'),
    ]

    operations = [
        migrations.AlterField(
            model_name='brainregion',
            name='is_super_group',
            field=models.BooleanField(blank=True, default=False, verbose_name='self'),
        ),
    ]
