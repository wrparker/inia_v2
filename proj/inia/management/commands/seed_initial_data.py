from django.core.management.base import BaseCommand, CommandError
from inia.models import Publication, IniaGene, Homologene, Dataset, GeneAliases
from datetime import datetime
import pandas as pd
import os

class Command(BaseCommand):
    help = 'Seeds initial data for database application.  Should only be used initially and then disbaled.'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        _INIT_DATA_DIRECTORY = os.path.join(os.path.dirname(__file__),
                                           '..',
                                           '..',
                                           '..',
                                           '..',
                                           'data_seed',
                                           'flat_data',
                                           '{}')
        #print (_INIT_DATA_DIRECTORY.format('publications.tsv'))
            # Publications first...

        if not Publication.objects.all():
            pubs = pd.read_csv(_INIT_DATA_DIRECTORY.format('publications.tsv'), sep='\t', engine='python')
            for index, row in pubs.iterrows():
                Publication.objects.create(
                    legacy_id=row['legacy_id'],
                    authors=row['authors'].strip('"'),
                    title=row['title'].strip('"'),
                    journal=row['journal'].strip('"'),
                    pages=row['pages'],
                    doi=row['doi'].strip('"'),
                    url=row['url'].strip('"'),
                    display=row['display'].strip('"'),
                    htmlid=row['htmlid'].strip('"'),
                    date_sub=datetime.strptime(row['date'], '%Y-%M-%d')
                )
        else:
            print ("Publication entries exist... skipping.")

        # Import Datasets.
        if not Dataset.objects.all():
            datasets = pd.read_csv(_INIT_DATA_DIRECTORY.format('datasets.tsv'), sep='\t', engine='python')
            for index, row in datasets.iterrows():
                related_pub = Publication.objects.get(legacy_id=row['publication'])
                Dataset.objects.create(
                    legacy_id=row['legacy_id'],
                    name=row['name'].strip('"'),
                    treatment=row['treatment_type'].strip('"').upper(),
                    publication=related_pub)
        else:
            print("Dataset entries exist... skipping.")

        # Import homologenes
        species = {
            '9606': 'HOMO SAPIENS',
            '10090': 'MUS MUSCULUS',
            '10116': 'RATTUS NORVEGICUS',
        }
        if not Homologene.objects.all():
            homologenes = pd.read_csv(_INIT_DATA_DIRECTORY.format('homologene_reduced.data'), sep='\t', engine='python')
            lines = []
            print ("Opening HID BRain file..")
            with open(_INIT_DATA_DIRECTORY.format('HID_Brain.txt', 'r')) as f:
                lines = f.read().splitlines()
            lines = [int(i) for i in lines]

            print ("Creating homologenes.... this make take a while.")
            homologene_items = []
            for index, row in homologenes.iterrows():
                # Faster to make them all in memory first...
                homologene_items.append(
                    Homologene(
                    homologene_group_id=row['h_id'],
                    gene_symbol=row['genesymbol'].strip(),
                    species=species[str(row['tax_id'])],
                    brain=(True if int(row['h_id']) in lines else False) )
                )
            Homologene.objects.bulk_create(homologene_items)
            print ("Success!")
        else:
            print("Information already exists for homologenes... not fililing")

        # Import IniaGenes... fun one now :o

        if not IniaGene.objects.all():
            print ("Constructing Inia genes and gene relationships.")
            lines = []
            with open(_INIT_DATA_DIRECTORY.format('genes.tsv')) as f:
                lines = f.readlines()
            # \N was encoded for null c haracters so watch out and also strip quotes......

            for line in lines[1:]:  #skip headers.
                row = line.split('\t')

                values = {
                    'microarray': row[0],
                    'model': row[1],
                    'phenotype': row[2],
                    'species': row[3],
                    'brainRegion': row[4],
                    'paradigm': row[5],
                    'paradigmDuration': row[6],
                    'alcohol': row[7],
                    'uniqueID': row[8],
                    'geneSymbol': row[9],
                    'geneName': row[10],
                    'pvalue': row[11],
                    'fdr': row[12],
                    'direction': row[13],
                    'pub': row[14],
                    'dataset': row[15],
                    'aliases': row[16],
                    'updated': row[17],
                    'conversion': row[18],
                    'legacy_id': row[19],
                }

                # Quick Formatting...
                for i, s in values.items():
                    values[i] = s.strip('"').strip(' ').replace('\\N', '')



                # Select Species...
                if values['species'].lower() == 'mouse':
                    values['species'] = 'MUS MUSCULUS'
                elif values['species'].lower() == 'human':
                    values['species'] = 'HOMO SAPIENS'
                elif values['species'].lower() == 'rat':
                    values['species'] = 'RATTUS NORVEGICUS'
                #Formatting done now lets create this stuff.
                relevant_pub = Publication.objects.get(legacy_id=values['pub'])
                relevant_dataset = Dataset.objects.get(legacy_id=values['dataset'])
                try:
                    if values['pvalue']:  #Null ch eck
                        values['pvalue'] = float(values['pvalue'])
                    else:
                        values['pvalue'] = None
                except:
                    print("Couldn't float {} on gene {}-{}".format(values['pvalue'], values['geneSymbol'], values['legacy_id']))
                    exit(0)
                newGene = IniaGene.objects.create(
                    legacy_id=values['legacy_id'],
                    uniqueID=values['uniqueID'],
                    microarray=values['microarray'],
                    model=values['model'],
                    phenotype=values['phenotype'],
                    species=values['species'],
                    brain_region= values['brainRegion'],
                    paradigm = values['paradigm'],
                    paradigm_duration = values['paradigmDuration'],
                    alcohol=(True if values['alcohol'].lower().strip()=='yes' else False),
                    gene_symbol=values['geneSymbol'],
                    gene_name=values['geneName'],
                    p_value=values['pvalue'],
                    fdr=float(values['fdr']),
                    direction=values['direction'],
                    publication=relevant_pub,
                    dataset=relevant_dataset,
                )

                for alias in values['aliases'].split(','):
                    # Ignore the dash.
                    if alias.strip() != '-' and alias.strip():
                        GeneAliases.objects.create(symbol=alias, IniaGene=newGene)

                # Now Add conversions (homologenes).
                homogenes = Homologene.objects.filter(homologene_group_id=values['conversion'])
                newGene.homologenes.add(*list(homogenes))
