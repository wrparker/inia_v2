from django.core.management.base import BaseCommand, CommandError
from inia.models import Publication, IniaGene, Homologene, Dataset, GeneAliases, BrainRegion, SpeciesType
from datetime import datetime
from multiprocessing.pool import ThreadPool as Pool
import pandas as pd
import os
import logging
import uuid
import mygene
from time import sleep

_LOG = logging.getLogger('application.'+__name__)

# Simultaneous http requests to mygene.info
def gene_info_worker(gene):
    mg = mygene.MyGeneInfo()
    species = ''
    if gene.dataset.species == SpeciesType.HOMO_SAPIENS:
        species = 'human'
    if gene.dataset.species == SpeciesType.MUS_MUSCULUS:
        species = 'mouse'
    if gene.dataset.species == SpeciesType.RATTUS_NORVEGICUS:
        species = 'rat'
    query = 'symbol:{}'.format(gene.gene_symbol)

    result = mg.query(query, species=species)
    if len(result['hits']) == 0:
        _LOG.info("WARNING IT WAS 0, info: {}".format(result['hits']))
    else:
        for hit in result['hits']:
            try:
                if gene.ncbi_uid == None:
                    gene.ncbi_uid = hit['entrezgene']
                    gene.save()
                    _LOG.info("Set entrezgene for {}:{} to {} .".format(gene.gene_symbol, species, hit['entrezgene']))
                else:
                    _LOG.info("ERROR!  Tried to replace ncbi_uid {} with {} for {}:{}".format(gene.ncbi_uid,
                                                                                              hit['entrezgene'],
                                                                                              gene.gene_symbol,
                                                                                              species))
                    gene.ncbi_uid = None
                    gene.save()
            except KeyError:
                continue



# move this out to a worker function so we can do this a little faster with threading.
def add_gene_worker(values):
    relevant_dataset = Dataset.objects.get(legacy_id=values['dataset'])
    newGene = IniaGene.objects.create(
        legacy_id=values['legacy_id'],
        probe_id=values['uniqueID'],
        gene_symbol=values['geneSymbol'],
        gene_name=values['geneName'],
        p_value=values['pvalue'],
        fdr=float(values['fdr']),
        direction=values['direction'],
        dataset=relevant_dataset,
    )

    for alias in values['aliases'].split(','):
        # Ignore the dash.
        if alias.strip() != '-' and alias.strip():
            GeneAliases.objects.create(symbol=alias, IniaGene=newGene)

    # Now Add conversions (homologenes).
    homogenes = Homologene.objects.filter(homologene_group_id=values['conversion'])
    newGene.homologenes.add(*list(homogenes))


class Command(BaseCommand):
    help = 'Seeds initial data for database application.  Should only be used initially and then disbaled.'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        '''
        This command should not be run, but not removing code for it incase it is needed in the future.  For now the
        command will exit if called to prevent accidenal calling.
        '''

        #_LOG.info("Preventing seed_initial_data from running.  Exiting 0")
        #exit(0)

        ''' Generate Brain Regions '''
        REGIONS = {
            'Striatum': ['Str'],
            'Accumbens': ['Acc'],
            'Accumbens Core': ['AccC'],
            'Accumbens Shell': ['AccSh'],
            'Amygdala': ['Amy'],
            'Basolateral Amygdala': ['BA'],
            'Central Amygdala': ['CA'],
            'Cerebellum': ['Cer'],
            'Frontal Cortex': ['FC'],
            'Hippocampus': ['Hip'],
            'Olfactory Bulb': ['OB'],
            'Stria Terminalis': ['BNST'],
            'Ventral Midbrain': ['VM'],
            'Ventral Tegmental Area': ['VTA'],
            'Whole Brain': ['WB']}
        if not BrainRegion.objects.all():
            for key, value in REGIONS.items():
                br = BrainRegion.objects.create(name=key,
                                                abbreviation=value[0])




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
                try:
                    related_brain_region = BrainRegion.objects.get(
                        name=datasetInfo[str(row['legacy_id'])]['brain_region']
                    )
                except:
                    related_brain_region = False
                official_dataset_name = "???"
                if related_pub.htmlid == 'fer2017':
                    official_dataset_name ='fer2017none_'+related_brain_region.abbreviation
                elif related_pub.htmlid == 'ost2013':
                    official_dataset_name = 'ost2013'
                    if row['treatment_type'].strip('"').lower() == 'chronic':
                        official_dataset_name += 'chronic'
                    else:
                        official_dataset_name += row['treatment_type'].strip('"').upper()
                    official_dataset_name += '_'
                    official_dataset_name += related_brain_region.abbreviation
                elif related_pub.htmlid == 'pon2012':
                    official_dataset_name = 'pon2012' + row['treatment_type'].strip('"').upper() + '_' + related_brain_region.abbreviation
                elif related_pub.htmlid == 'mul2011':
                    if related_brain_region == False:
                        official_dataset_name = 'mul2011' + row['treatment_type'].strip(
                            '"').upper() + '_Str'
                    else:
                        official_dataset_name = 'mul2011' + row['treatment_type'].strip(
                            '"').upper() + '_' + related_brain_region.abbreviation
                elif related_pub.htmlid == 'kim2007':
                    official_dataset_name = 'kim2007none_'+related_brain_region.abbreviation
                elif related_pub.htmlid == 'mul2006':
                    official_dataset_name = 'mul2006none_'+related_brain_region.abbreviation

                normalized_treatment = row['treatment_type'].strip('"').upper()
                if normalized_treatment == '':
                    normalized_treatment = 'NONE'
                if not normalized_treatment:
                    normalized_treatment = 'NONE'
                Dataset.objects.create(
                    legacy_id=row['legacy_id'],
                    name=official_dataset_name,
                    treatment=row['treatment_type'].strip('"').upper(),
                    publication=related_pub,
                    microarray=datasetInfo[str(row['legacy_id'])]['microarray'],
                    model=datasetInfo[str(row['legacy_id'])]['model'],
                    phenotype=datasetInfo[str(row['legacy_id'])]['phenotype'],
                    species=datasetInfo[str(row['legacy_id'])]['species'],
                    paradigm=datasetInfo[str(row['legacy_id'])]['paradigm'],
                    paradigm_duration=datasetInfo[str(row['legacy_id'])]['paradigm_duration'],
                    alcohol=datasetInfo[str(row['legacy_id'])]['alcohol'],
                )
                print (official_dataset_name)

            for br in BrainRegion.objects.all():
                if br.name == "Accumbens":
                    ds = Dataset.objects.get(name='fer2017none_AccC')
                    ds.brain_regions.add(br)
                    ds.save()
                    ds = Dataset.objects.get(name='fer2017none_AccSh')
                    ds.brain_regions.add(br)
                    ds.save()
                    ds = Dataset.objects.get(name='kim2007none_Acc')
                    ds.brain_regions.add(br)
                    ds.save()
                    ds = Dataset.objects.get(name='mul2011DID_Str')
                    ds.brain_regions.add(br)
                elif br.name == "Accumbens Core":
                    ds = Dataset.objects.get(name='fer2017none_AccC')
                    ds.brain_regions.add(br)
                elif br.name == 'Accumbens Shell':
                    ds = Dataset.objects.get(name='fer2017none_AccSh')
                    ds.brain_regions.add(br)
                elif br.name == 'Amygdala':
                    dss = ['fer2017none_BA', 'fer2017none_CA', 'kim2007none_Amy', 'pon2012CIA_BA', 'pon2012CIA_CA']
                    for ds1 in dss:
                        ds = Dataset.objects.get(name=ds1)
                        ds.brain_regions.add(br)
                elif br.name == 'Basolateral Amygdala':
                    dss = ['fer2017none_BA', 'pon2012CIA_BA']
                    for ds1 in dss:
                        ds = Dataset.objects.get(name=ds1)
                        ds.brain_regions.add(br)
                elif br.name == 'Central Amygdala':
                    dss = ['fer2017none_CA', 'pon2012CIA_CA']
                    for ds1 in dss:
                        ds = Dataset.objects.get(name=ds1)
                        ds.brain_regions.add(br)
                elif br.name == 'Cerebellum':
                    dss = ['mul2011DID_Cer']
                    for ds1 in dss:
                        ds = Dataset.objects.get(name=ds1)
                        ds.brain_regions.add(br)
                elif br.name == 'Frontal Cortex':
                    dss = ['fer2017none_FC',
                           'kim2007none_FC',
                           'mul2011DID_FC',
                           'ost2013chronic_FC',
                           'ost2013DID_FC',
                           'ost2013EOD_FC',
                           'ost2013LPS_FC',
                           'pon2012CIA_FC' ]
                    for ds1 in dss:
                        ds = Dataset.objects.get(name=ds1)
                        ds.brain_regions.add(br)
                elif br.name == 'Hippocampus':
                    dss = ['kim2007none_Hip',
                           'mul2011DID_Hip' ]
                    for ds1 in dss:
                        ds = Dataset.objects.get(name=ds1)
                        ds.brain_regions.add(br)
                elif br.name == 'Olfactory Bulb':
                    dss = ['mul2011DID_OB']
                    for ds1 in dss:
                        ds = Dataset.objects.get(name=ds1)
                        ds.brain_regions.add(br)
                elif br.name == 'Stria Terminalis':
                    dss = ['fer2017none_BNST']
                    for ds1 in dss:
                        ds = Dataset.objects.get(name=ds1)
                        ds.brain_regions.add(br)
                elif br.name == 'Striatum':
                    dss = ['mul2011DID_Str']
                    for ds1 in dss:
                        ds = Dataset.objects.get(name=ds1)
                        ds.brain_regions.add(br)
                elif br.name == 'Ventral Midbrain':
                    dss = ['mul2011DID_VM']
                    for ds1 in dss:
                        ds = Dataset.objects.get(name=ds1)
                        ds.brain_regions.add(br)
                elif br.name == 'Ventral Tegmental Area':
                    dss = ['fer2017none_VTA']
                    for ds1 in dss:
                        ds = Dataset.objects.get(name=ds1)
                        ds.brain_regions.add(br)
                elif br.name == 'Whole Brain':
                    dss = ['kim2007none_WB', 'mul2006none_WB']
                    for ds1 in dss:
                        ds = Dataset.objects.get(name=ds1)
                        ds.brain_regions.add(br)

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
                    brain=(True if int(row['h_id']) in lines else False),
                    ncbi_uid=row['enterez_id']
                    )
                )
            Homologene.objects.bulk_create(homologene_items)
            _LOG.info ("Success!")
        else:
            _LOG.info("Information already exists for homologenes... not fililing")

        # Import IniaGenes... fun one now :o

        if not IniaGene.objects.all():
            _LOG.info ("Constructing Inia genes and gene relationships.")



            pool = Pool(10)
            for values in geneValueList:
                pool.apply_async(add_gene_worker, (values,))
            pool.close()
            pool.join()

        else:
            _LOG.info("Skipping INIA genes since values already exist.")

        _LOG.info("Adding ncbi_UIDs (enterez ids)")
        needs_ncbi_uid = []
        for i in IniaGene.objects.all().exclude(gene_symbol='').exclude(gene_symbol__isnull=True).exclude(ncbi_uid__isnull=False):
            try:
                i.ncbi_uid = i.homologenes.get(gene_symbol__iexact=i.gene_symbol, species=i.dataset.species).ncbi_uid
                i.save()
            except Homologene.DoesNotExist:
                needs_ncbi_uid.append(i)
            except Homologene.MultipleObjectsReturned:
                for f in i.homologenes.filter(species=i.dataset.species):
                    _LOG.info('{} {} {}'.format(f.gene_symbol, f.species, f.ncbi_uid))
                exit(1)
                #ncbi_uids = i.homologenes.filter(species=i.dataset.species).values_list('ncbi_uid', flat=True)
                #if len(set(ncbi_uids)) == 1:


        _LOG.info("QUERYING FOR INFO")
        pool = Pool(10)
        for gene in needs_ncbi_uid:
            pool.apply_async(gene_info_worker, (gene,))
        pool.close()
        pool.join()

        _LOG.info("Get UIDs stuff... no renamign done")
        sleep(10)  # avoid overwhelming the API.

        mg = mygene.MyGeneInfo()
        for gene in IniaGene.objects.filter(ncbi_uid__isnull=True).exclude(gene_symbol='').exclude(gene_symbol__isnull=True):
            species = ''
            if gene.dataset.species == SpeciesType.HOMO_SAPIENS:
                species = 'human'
            if gene.dataset.species == SpeciesType.MUS_MUSCULUS:
                species = 'mouse'
            if gene.dataset.species == SpeciesType.RATTUS_NORVEGICUS:
                species = 'rat'
            result = mg.query('alias:{}'.format(gene.gene_symbol), species=species)
            if len(result['hits']) == 0:
                _LOG.debug("No hit found {}:{}".format(gene.gene_symbol, gene.dataset.species))
            else:
                for hit in result['hits']:
                    try:
                        if gene.ncbi_uid == None:
                            gene.ncbi_uid = hit['entrezgene']
                            gene.save()
                            _LOG.info("Set entrezgene for ALIAS {}:{} to {} .".format(gene.gene_symbol, species,
                                                                                hit['entrezgene']))
                        else:
                            _LOG.info("ERROR!  Tried to replace ncbi_uid {} with {} for {}:{} -- UNSETTING!".format(gene.ncbi_uid,
                                                                                                      hit['entrezgene'],
                                                                                                      gene.gene_symbol,
                                                                                                      species))
                            gene.ncbi_uid = None
                            gene.save()
                    except KeyError:
                        continue

        #TODO Discontinued genes/unfound genes with a gene symbol need to be populated, we need to handle unset genes here or osmething...
        # TODO: manual inspection?
         # ???

        # Now lets fix any broken homologenes from update to new version.
        no_homologene = IniaGene.objects.filter(gene_symbol__isnull=False).exclude(gene_symbol='').exclude(ncbi_uid__isnull=True)

        for gene in no_homologene:
            try:
                hg = Homologene.objects.get(ncbi_uid=gene.ncbi_uid)
                hgs = Homologene.objects.filter(homologene_group_id=hg.homologene_group_id)
                gene.homologenes.add(*list(hgs))  # add them all.
                _LOG.info('added {} to {} ({})'.format(hg.gene_symbol, gene.gene_symbol, gene.ncbi_uid))
            except:
                _LOG.info("no homologene found for uid {}".format(gene.ncbi_uid))
        _LOG.info("done!")


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


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
