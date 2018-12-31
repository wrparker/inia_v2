from django.core.management.base import BaseCommand, CommandError
from inia.models import Publication, IniaGene, Homologene, Dataset, GeneAliases
from datetime import datetime
import pandas as pd
import os
import logging

_LOG = logging.getLogger('application.'+__name__)

class Command(BaseCommand):
    help = 'Seeds initial data for database application.  Should only be used initially and then disbaled.'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        '''
        This command should not be run, but not removing code for it incase it is needed in the future.  For now the
        command will exit if called to prevent accidenal calling.
        '''

        _LOG.info("Preventing seed_initial_data from running.  Exiting 0")
        exit(0)


        _INIT_DATA_DIRECTORY = os.path.join(os.path.dirname(__file__),
                                           '..',
                                           '..',
                                           '..',
                                           '..',
                                           'data_seed',
                                           'flat_data',
                                           '{}')

        # Publications first...

        # Gotta push stuff into Dataset.
        geneValueList = getGeneValues(_INIT_DATA_DIRECTORY.format('genes.tsv'))
        datasetInfo = getDatasetVals(geneValueList)

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
            _LOG.info ("Publication entries exist... skipping.")

        # Import Datasets.
        if not Dataset.objects.all():
            datasets = pd.read_csv(_INIT_DATA_DIRECTORY.format('datasets.tsv'), sep='\t', engine='python')
            for index, row in datasets.iterrows():
                related_pub = Publication.objects.get(legacy_id=row['publication'])
                Dataset.objects.create(
                    legacy_id=row['legacy_id'],
                    name=row['name'].strip('"'),
                    treatment=row['treatment_type'].strip('"').upper(),
                    publication=related_pub,
                    microarray=datasetInfo[str(row['legacy_id'])]['microarray'],
                    model=datasetInfo[str(row['legacy_id'])]['model'],
                    phenotype=datasetInfo[str(row['legacy_id'])]['phenotype'],
                    species=datasetInfo[str(row['legacy_id'])]['species'],
                    brain_region=datasetInfo[str(row['legacy_id'])]['brain_region'],
                    paradigm=datasetInfo[str(row['legacy_id'])]['paradigm'],
                    paradigm_duration=datasetInfo[str(row['legacy_id'])]['paradigm_duration'],
                    alcohol=datasetInfo[str(row['legacy_id'])]['alcohol'],
                )
        else:
            _LOG.info("Dataset entries exist... skipping.")

        # Import homologenes
        species = {
            '9606': 'HOMO SAPIENS',
            '10090': 'MUS MUSCULUS',
            '10116': 'RATTUS NORVEGICUS',
        }
        if not Homologene.objects.all():
            homologenes = pd.read_csv(_INIT_DATA_DIRECTORY.format('homologene_reduced.data'), sep='\t', engine='python')
            lines = []
            _LOG.info ("Opening HID BRain file..")
            with open(_INIT_DATA_DIRECTORY.format('HID_Brain.txt', 'r')) as f:
                lines = f.read().splitlines()
            lines = [int(i) for i in lines]

            _LOG.info ("Creating homologenes.... this make take a while.")
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
            _LOG.info ("Success!")
        else:
            _LOG.info("Information already exists for homologenes... not fililing")

        # Import IniaGenes... fun one now :o

        if not IniaGene.objects.all():
            _LOG.info ("Constructing Inia genes and gene relationships.")


            for values in geneValueList:
                #Formatting done now lets create this stuff.
                relevant_pub = Publication.objects.get(legacy_id=values['pub'])
                relevant_dataset = Dataset.objects.get(legacy_id=values['dataset'])

                newGene = IniaGene.objects.create(
                    legacy_id=values['legacy_id'],
                    uniqueID=values['uniqueID'],
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
        else:
            _LOG.info("Skipping INIA genes since values already exist.")


def getGeneValues(genes_tsv):
    lines = []
    values = []
    with open(genes_tsv) as f:
        lines = f.readlines()
    # \N was encoded for null c haracters so watch out and also strip quotes......

    for line in lines[1:]:  # skip headers.
        row = line.split('\t')

        value = {
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

        for i, s in value.items():
            value[i] = s.strip('"').strip(' ').replace('\\N', '')

        # Select Species...
        if value['species'].lower() == 'mouse':
            value['species'] = 'MUS MUSCULUS'
        elif value['species'].lower() == 'human':
            value['species'] = 'HOMO SAPIENS'
        elif value['species'].lower() == 'rat':
            value['species'] = 'RATTUS NORVEGICUS'

        try:
            if value['pvalue']:  #Null ch eck
                value['pvalue'] = float(value['pvalue'])
            else:
                value['pvalue'] = None
        except:
            _LOG.error("Couldn't float {} on gene {}-{}".format(value['pvalue'], value['geneSymbol'], value['legacy_id']))
            exit(0)
        values.append(value)

    return values


def getDatasetVals(geneValueList):
    datasetInfo = {}

    for val in geneValueList:
        if not datasetInfo.get(str(val['dataset']), None):
            datasetInfo[str(val['dataset'])] = {
                'microarray': val['microarray'],
                'model': val['model'],
                'phenotype': val['phenotype'],
                'species': val['species'],
                'brain_region': val['brainRegion'],
                'paradigm': val['paradigm'],
                'paradigm_duration': val['paradigmDuration'],
                'alcohol': (True if val['alcohol'].lower().strip() == 'yes' else False)
            }
    print (datasetInfo)
    return datasetInfo
