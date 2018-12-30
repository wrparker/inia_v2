# Generated by Django 2.0.6 on 2018-12-30 03:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Dataset',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('legacy_id', models.IntegerField()),
                ('name', models.CharField(max_length=100)),
                ('treatment', models.CharField(choices=[('DID', 'DID'), ('NONE', 'NONE'), ('CIA', 'CIA'), ('EOD', 'EOD'), ('LPS', 'LPS')], max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='GeneAliases',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('symbol', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Homologene',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('homologene_group_id', models.IntegerField()),
                ('gene_symbol', models.CharField(max_length=255)),
                ('created_at', models.DateField(auto_now=True)),
                ('updated_at', models.DateField(auto_now=True)),
                ('species', models.CharField(choices=[('HOMO SAPIENS', 'HOMO SAPIENS'), ('MUS MUSCULUS', 'MUS MUSCULUS'), ('RATTUS NORVEGICUS', 'RATTUS NORVEGICUS')], max_length=255)),
                ('brain', models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='IniaGene',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('legacy_id', models.IntegerField()),
                ('uniqueID', models.CharField(max_length=255)),
                ('microarray', models.CharField(max_length=255)),
                ('model', models.CharField(max_length=255)),
                ('phenotype', models.CharField(max_length=255)),
                ('species', models.CharField(choices=[('HOMO SAPIENS', 'HOMO SAPIENS'), ('MUS MUSCULUS', 'MUS MUSCULUS'), ('RATTUS NORVEGICUS', 'RATTUS NORVEGICUS')], max_length=255)),
                ('brain_region', models.CharField(max_length=255)),
                ('paradigm', models.CharField(max_length=255)),
                ('paradigm_duration', models.CharField(max_length=255)),
                ('alcohol', models.BooleanField()),
                ('gene_symbol', models.CharField(max_length=255)),
                ('gene_name', models.CharField(max_length=255)),
                ('p_value', models.FloatField()),
                ('fdr', models.FloatField()),
                ('direction', models.CharField(choices=[('UP', 'UP'), ('DOWN', 'DOWN')], max_length=255)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('dataset', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='inia.Dataset')),
            ],
        ),
        migrations.CreateModel(
            name='Publication',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('legacy_id', models.IntegerField()),
                ('authors', models.TextField()),
                ('title', models.CharField(max_length=255)),
                ('journal', models.CharField(max_length=255)),
                ('pages', models.CharField(max_length=15)),
                ('date_sub', models.DateTimeField()),
                ('doi', models.CharField(max_length=255)),
                ('url', models.CharField(max_length=255)),
                ('display', models.CharField(max_length=255)),
                ('htmlid', models.CharField(max_length=255)),
            ],
        ),
        migrations.AddField(
            model_name='iniagene',
            name='publication',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='inia.Publication'),
        ),
        migrations.AddField(
            model_name='genealiases',
            name='IniaGene',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inia.IniaGene'),
        ),
        migrations.AddField(
            model_name='dataset',
            name='publication',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='inia.Publication'),
        ),
    ]
