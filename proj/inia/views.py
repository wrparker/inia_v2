import tempfile
import csv
from django.http import HttpResponse
from urllib.parse import unquote, parse_qs, urlencode
from django.shortcuts import render
from django.db.models import F, Q
from django.core.paginator import Paginator
from .models import Publication, Dataset, BrainRegion, IniaGene, Homologene, SpeciesType
from .forms import ContactForm
from .analysis.search import base_gene_search, LegacyAPIHelper
from functools import reduce
import scipy.stats as stats

import logging

_LOG = logging.getLogger('application.'+ __name__)

_ALLOWED_TRUE_BOOLEANS = ['yes', '1', 'true']


def index(request):
    return render(request, 'home.html', {})


def analysis_home(request):
    return render(request, 'analysis_home.html', {})


def about(request):
    return render(request, 'about.html', {})


def contact(request):
    return render(request, 'contact.html', {'contact_form': ContactForm()})


def links(request):
    return render(request, 'links.html', {})

def help_home(request):
    return render(request, 'help_home.html', {})


def datasets(request):
    publications = Publication.objects.all().order_by('-date_sub')
    brain_regions = BrainRegion.objects.all().order_by('name')
    info_by_region = {}
    for region in brain_regions:
        info_by_region[region.name] = {}
        info_by_region[region.name]['name'] = region.name
        info_by_region[region.name]['datasets'] = list(region.dataset_set.all().order_by('name'))
        info_by_region[region.name]['total'] = 0
        for ds in info_by_region[region.name]['datasets']:
            info_by_region[region.name]['total'] += ds.get_number_genes()
    return render(request, 'datasets.html', {'publications': publications,
                                             'info_by_region': info_by_region,
                                             'brain_regions': brain_regions})


# This should ideally be refactored out into a proper API, but we need to provide legacy support...
# THis is kind of ugly as is...
def search(request):
    ''' Regex Values are allowed... separated by pipe?... it doesn't seem to work on normal'''
    output = request.GET.get('output', '')
    output = output.lower()
    _err_msg = 'API Error: Parmeter: {} -- Value Received: {} -- Expected: {}'
    errors = []
    for param in request.GET:
        if param not in LegacyAPIHelper.ALLOWED_API_PARAMETERS:
            errors.append('Unexpected parameter given: {}={}'.format(param, request.GET.get(param)))

    gene_param = request.GET.get('gene', None)
    if gene_param:
        gene_param = unquote(gene_param)
        genes = base_gene_search(gene_param, exclude_name=request.GET.get('excludeName', False))
    else:
        # is there a param?
        genes = False
        for param in LegacyAPIHelper.ADVANCED_FILTER_OPTIONS:
            if request.GET.get(param, None):
                genes = True
        if genes:
            genes = IniaGene.objects.all()
    if genes:
        for api_param in LegacyAPIHelper.ADVANCED_FILTER_OPTIONS:
            value = request.GET.get(api_param, None)
            if api_param in request.GET and value:
                valid, unique_vals = LegacyAPIHelper.check_and_return_valid_values(api_param, value)
                if valid:
                    genes = LegacyAPIHelper.perform_filter(api_param, genes, value)
                else:
                    genes = IniaGene.objects.none()
                    errors.append(_err_msg.format(api_param, value, ', '.join(unique_vals)))

        genes = genes.order_by(F('gene_symbol').asc(nulls_last=True)) if genes else IniaGene.objects.none()
        # TODO: how can we make this more faster/effective with less queries.
        genes = genes.prefetch_related('dataset', 'homologenes', 'dataset__publication', 'genealiases_set', 'dataset__brain_regions').all()
        total_results = genes.count()
        if output == 'html':
            # Only paginate HTML format.
            paginator = Paginator(genes, 100)
            page = request.GET.get('page', 1)
            query = request.GET.urlencode()
            query = parse_qs(query)
            query.pop('page', None)
            query.pop('output', None)
            query = urlencode(query, doseq=True)
            genes = paginator.get_page(page)
            return render(request, 'search.html', {'genes': genes,
                                                   'urlencode': query,
                                                   'total_results': total_results,
                                                   'errors': errors
                                                   })
        else:  #if we don't recognize 'html' or whatever we just make it a csv, return the file.
            # convert to dict...
            output = []
            for gene in genes:
                gene_info = {}
                gene_info['NCBI UID'] = gene.ncbi_uid
                gene_info['Gene Symbol'] = gene.ncbi_uid
                gene_info['Gene Name'] = gene.ncbi_uid
                gene_info['aliases'] = ', '.join(gene.genealiases_set.all().values_list('symbol', flat=True))
                gene_info['Homologene Id'] = gene.get_homologene_id()
                gene_info['Human Orthologs'] = gene.list_human_orthologs()
                gene_info['Rat Orthologs'] = gene.list_rat_orthologs()
                gene_info['Mouse Orthologs'] = gene.list_mouse_orthologs()
                gene_info['Gene Expression Platform'] = gene.dataset.microarray
                gene_info['Probe Id'] = gene.probe_id
                gene_info['Species'] = gene.dataset.species
                gene_info['Ethanol/Treatment'] = gene.dataset.treatment
                gene_info['Brain region/Cell type'] = ','.join([f.name for f in gene.dataset.brain_regions.all()])
                gene_info['P-value'] = gene.p_value
                gene_info['Direction of Change'] = gene.direction
                gene_info['Est FDR'] = gene.fdr
                gene_info['Dataset'] = gene.dataset.name
                gene_info['Reference'] = gene.dataset.publication.get_short_name()
                output.append(gene_info)
            result_file = dict_list_to_csv(output)
            response = HttpResponse(content=open(result_file, 'rb'))
            response['Content-Type'] = 'text'
            response['Content-Disposition'] = 'attachment; filename="results.csv"'
            return response
    else:
        return render(request, 'search.html', {'errors': errors})


def boolean_dataset(request):
    # TODO: dataset comprised of the smaller (fer2017, etc...)
    selected_ds = [ds for ds in request.GET.getlist('ds') if ds != '']
    selected_br = [br for br in request.GET.getlist('br') if br != '']
    if not request.GET.get('operation') or not selected_ds or len(selected_ds) <= 1:
        brain_regions = BrainRegion.objects.all().order_by('name')
        publications = Publication.objects.all().order_by('-date_sub').prefetch_related('dataset_set')
        return render(request, 'boolean_dataset.html', {'brain_regions': brain_regions,
                                                        'publications': publications})
    else:
        data_sets = Dataset.objects.filter(pk__in=selected_ds).prefetch_related('iniagene_set')
        brain_regions = [BrainRegion.objects.get(pk=br) for br in selected_br]
        brain_region_names = ', '.join([br.name for br in brain_regions])
        dataset_names = ', '.join([ds.name for ds in data_sets])
        operation = request.GET.get('operation')

        if operation:
            qs = []
            allowed_result = []
            for ds in data_sets:
                homologenes = set(ds.iniagene_set.exclude(homologenes=None).values_list('homologenes__homologene_group_id', flat=True))
                if not allowed_result:  #  initialize it.
                    allowed_result.extend(homologenes)
                    allowed_result = set(allowed_result)
                else:
                    if operation == 'intersect':
                        allowed_result &= homologenes
                    elif operation == 'union':
                        allowed_result |= homologenes
                    if not allowed_result:
                        return render(request, 'boolean_dataset.html', {'results': {},
                                                                        'dataset_names': dataset_names,
                                                                        'brain_region_names': brain_region_names,
                                                                        'intersection_species': 'None'})

            d_list = map(lambda n: Q(dataset=n), data_sets)
            d_list = reduce(lambda a, b: a | b, d_list)

            h_list = map(lambda n: Q(homologenes__homologene_group_id=str(n)), list(allowed_result))
            h_list = reduce(lambda a, b: a | b, h_list)

            if selected_br:
                br_list = map(lambda n: Q(dataset__brain_regions=n), brain_regions)
                br_list = reduce(lambda a, b: a | b, br_list)

            if not selected_br:
                genes = IniaGene.objects.filter(Q(h_list) & Q(d_list)).prefetch_related('homologenes', 'dataset')
            else:
                genes = IniaGene.objects.filter(Q(h_list) & Q(d_list) & Q(br_list)).prefetch_related('homologenes', 'dataset')

            if not genes:   # br filter caused no genes.
                return render(request, 'boolean_dataset.html', {'results': {},
                                                                'dataset_names': dataset_names,
                                                                'brain_region_names': brain_region_names,
                                                                'intersection_species': 'None'})

            intersection_species = None

            if len(set(genes.values_list('dataset__species', flat=True))) > 1:
                intersection_species = 'mixed species'
            else:
                intersection_species = genes[0].dataset.species + ' only'


            tmp = {}
            # Sort into a dictionary with homologene-id as key.
            for gene in genes:
                hgene_group_id = gene.get_homologene_id()
                if not hgene_group_id:
                    if not tmp.get(gene.probe_id): # use probe id since we don't have homologene...
                        tmp[gene.probe_id] = []
                    tmp[gene.probe_id].append(gene)
                else:
                    if not tmp.get(hgene_group_id):
                        tmp[hgene_group_id] = []
                    tmp[hgene_group_id].append(gene)

            results = []
            for h_id, genes in tmp.items():  # Result row.
                row = {}
                # Use first element to get the universal information...

                row['human'] = genes[0].list_human_orthologs()
                row['mouse'] = genes[0].list_mouse_orthologs()
                row['rat'] = genes[0].list_rat_orthologs()
                row['homologene_id'] = h_id

                if operation == 'intersect':
                    # direction per dataset:
                    ds_directions = {}
                    for gene in genes:
                        if not ds_directions.get(gene.dataset.name):
                            ds_directions[gene.dataset.name] = gene.direction
                        elif ds_directions[gene.dataset.name] != gene.direction:
                            ds_directions[gene.dataset.name] = 'BOTH'
                    directions = [direction for dataset, direction in ds_directions.items()]

                    row['directions_per_dataset'] = ', '.join(directions)
                    if len(set(directions)) > 1:
                        row['overall_direction'] = 'DIFF'
                    else:
                        row['overall_direction'] = 'SAME'

                elif operation == 'union':  # pubs per item
                    row['datasets'] = ', '.join(set([gene.dataset.name for gene in genes]))

                results.append(row)

            results = sorted(results, key=lambda k: k['human'])  # Sort by human key.

            if(request.GET.get('output') == 'csv'):
                result_file = dict_list_to_csv(results)
                response = HttpResponse(content=open(result_file, 'rb'))
                response['Content-Type'] = 'text'
                response['Content-Disposition'] = 'attachment; filename="results.csv"'
                return response

            csv_url = request.GET.urlencode()
            csv_url = parse_qs(csv_url)
            csv_url['output'] = 'csv'
            csv_url = urlencode(csv_url, doseq=True)

            # Stats table:
            intersection_stats = {}
            if operation == 'intersect' and data_sets.count() == 2:
                intersection_stats['ds1_name'] = data_sets[0].name
                intersection_stats['ds1_num'] = len(set(data_sets[0].iniagene_set.exclude(homologenes=None).values_list('homologenes__homologene_group_id', flat=True)))
                intersection_stats['ds2_name'] = data_sets[1].name
                intersection_stats['ds2_num'] = len(set(data_sets[1].iniagene_set.exclude(homologenes=None).values_list('homologenes__homologene_group_id', flat=True)))
                # TODO: Figure out genes in background
                ''' Okay the background is the number of "conversions" or homologenes for that species of the dataset for each species involved...
                Only count 1x per homologene group id.  Species must be present in homologene to be considered background.
                '''
                background = Homologene.objects.filter(Q(species=data_sets[0].species) | Q(species=data_sets[1].species)).values_list('homologene_group_id', flat=True)
                intersection_stats['background'] = len(set(background))
                # TODO: Figure out hypergeometric score
                # l = backgroud genes, k = genes in ds1, q = overlap, m = genes in ds2
                # cat(formatC(phyper((q-1),m,(l-m),k,lower.tail=FALSE), digits=3, format="g", flag="#"));
                # https://gist.github.com/crazyhottommy/67179a5f2925794a09d8#file-gene_sets_hypergeometric_test-py
                # That was translated to python...
                # params, (overlap - 1), background, ds1_size, ds2_sizee
                intersection_stats['hypergeometric_score'] = stats.hypergeom.sf(len(results) - 1,
                                                                                intersection_stats['background'],
                                                                                intersection_stats['ds1_num'],
                                                                                intersection_stats['ds2_num'])
                intersection_stats['mark_score'] = intersection_stats['hypergeometric_score'] <= 0.05  # bool.
                intersection_stats['hypergeometric_score'] = '{0:1.4g}'.format(intersection_stats['hypergeometric_score'])




            return render(request, 'boolean_dataset.html', {'results': results,
                                                            'dataset_names': dataset_names,
                                                            'brain_region_names': brain_region_names,
                                                            'intersection_species': intersection_species,
                                                            'intersection_stats': intersection_stats,
                                                            'csv_url': csv_url})

def dict_list_to_csv(dict_list):
    '''
    :param dict_list: A list of dictionaries
    :return: None if invalid input, file location if valid.
    '''
    if len(dict_list) < 1:
        return None
    keys = dict_list[0].keys()
    tmp_file = tempfile.mkstemp(suffix='.csv', prefix='output')
    with open(tmp_file[1], 'w') as f:
        dict_writer = csv.DictWriter(f,
                                     fieldnames=keys,
                                     quoting=csv.QUOTE_ALL)
        dict_writer.writeheader()
        dict_writer.writerows(dict_list)
    return tmp_file[1]
