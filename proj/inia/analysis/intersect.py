import scipy.stats as stats
from django.db.models import Q
from inia.models import Homologene, IniaGene, Dataset
from functools import reduce


# TODO: Backgroudn homologenes needs to be filtered further to only homologenes expressed in the brain.

def bonferroni_factor():
    num_datasets = Dataset.objects.all().count()
    return (num_datasets * (num_datasets-1))/2


def num_intersect_gene(dataset1, dataset2):
    ''' Returns the number of intersecting genes between two datasets..'''
    potentials_1 = dataset1.iniagene_set.exclude(homologenes=None).values_list('homologenes__homologene_group_id', flat=True)
    potentials_2 = dataset2.iniagene_set.exclude(homologenes=None).values_list('homologenes__homologene_group_id', flat=True)
    overlapping_homologene_ids = set(set(potentials_1)  & set(potentials_2))

    if not overlapping_homologene_ids:
        # There is no intersection, stop.
        return 0

    d_list = map(lambda n: Q(dataset=n), [dataset1, dataset2])
    d_list = reduce(lambda a, b: a | b, d_list)

    h_list = map(lambda n: Q(homologenes__homologene_group_id=str(n)), list(overlapping_homologene_ids))
    h_list = reduce(lambda a, b: a | b, h_list)

    overlapping_genes = IniaGene.objects.filter(Q(h_list) & Q(d_list)).prefetch_related('homologenes')
    tmp = {}
    # Sort into a dictionary with homologene-id as key.
    return len(set([gene.get_homologene_id() for gene in overlapping_genes]))

def hypergeometric_score(dataset1, dataset2, num_overlap=False, return_params_as_dict=False):
    '''
    :param dataset1: dataset 1 being overlapped
    :param dataset2: dataset 2 being overlapped
    :param num_overlap: optional, if not provided, will be calculated, implemented for efficiency used in other places.
    :return: hypergeometric score
        # Notes...
        # l = backgroud genes, k = genes in ds1, q = overlap, m = genes in ds2
        # cat(formatC(phyper((q-1),m,(l-m),k,lower.tail=FALSE), digits=3, format="g", flag="#"));
        # https://gist.github.com/crazyhottommy/67179a5f2925794a09d8#file-gene_sets_hypergeometric_test-py
        # That was translated to python...
        # params, (overlap - 1), background, ds1_size, ds2_sizee
    '''

    if not num_overlap:
        num_overlap = num_intersect_gene(dataset1, dataset2)

    ds1_num_total = len(set(dataset1.iniagene_set.exclude(homologenes=None).values_list('homologenes__homologene_group_id', flat=True)))
    ds2_num_total = len(set(dataset2.iniagene_set.exclude(homologenes=None).values_list('homologenes__homologene_group_id', flat=True)))
    background = len(set(Homologene.objects.filter(Q(species=dataset1.species) | Q(species=dataset2.species)).values_list('homologene_group_id', flat=True)))
    score = stats.hypergeom.sf(num_overlap - 1, background, ds1_num_total, ds2_num_total)
    if not return_params_as_dict:
        return score
    else:
        intersection_stats = {}
        intersection_stats['hypergeometric_score'] = score
        intersection_stats['background'] = background
        intersection_stats['ds1_name'] = dataset1.name
        intersection_stats['ds2_name'] = dataset2.name
        intersection_stats['mark_score'] = (score <= 0.05)
        intersection_stats['num_overlap'] = num_overlap
        intersection_stats['ds1_num'] = ds1_num_total
        intersection_stats['ds2_num'] = ds2_num_total
        return intersection_stats


def custom_dataset_intersection (custom_genes, custom_species, dataset):
    '''This takes in a queryset of genes rather than 2 datasets and gives calculations. '''
    # TODO: FIx calculations here...
    print (custom_genes.count())
    intersect_stats = {}
    bonferroni_adj = bonferroni_factor()
    # only care about homoologenes as adjusted length.
    genes_length = len(set(custom_genes.exclude(homologenes=None).values_list('homologenes__homologene_group_id', flat=True)))
    background = len(set(Homologene.objects.filter(Q(species=custom_species) | Q(species=dataset.species)).values_list('homologene_group_id', flat=True)))
    # Only overlapping homologenes, count only once.
    num_overlap = len(set(custom_genes.filter(dataset=dataset).exclude(homologenes=None).values_list('homologenes__homologene_group_id', flat=True)))
    ds_len = len(set(dataset.iniagene_set.exclude(homologenes=None).values_list('homologenes__homologene_group_id', flat=True)))
    intersect_stats['hypergeometric_score'] = stats.hypergeom.sf(num_overlap - 1, background, genes_length, ds_len)
    intersect_stats['bonferroni'] = min(1, intersect_stats['hypergeometric_score']*bonferroni_factor())
    intersect_stats['standard_dataset_length'] = ds_len
    intersect_stats['custom_dataset_length'] = genes_length
    intersect_stats['overlap'] = num_overlap
    intersect_stats['background_homologenes'] = background
    return intersect_stats

def format_hypergeometric_score(score):
    if score < 0.01:
        return '%.2e' % score
    elif score < 0.1:
        return '%.4f' % score
    elif score < 1:
        return '%.3f' % score
    else:
        return '%.2f' % score





