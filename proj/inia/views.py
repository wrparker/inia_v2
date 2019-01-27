import tempfile
import csv
from django.http import HttpResponse
from urllib.parse import unquote, parse_qs, urlencode
from django.shortcuts import render
from django.db.models import F, Q
from django.core.paginator import Paginator
from .models import Publication, Dataset, BrainRegion, IniaGene
from .forms import ContactForm
from .analysis.search import base_gene_search, LegacyAPIHelper


import logging

_LOG = logging.getLogger('application.'+ __name__)

_ALLOWED_TRUE_BOOLEANS = ['yes', '1', 'true']


def index(request):
    return render(request, 'home.html', {})


def analysis_home(request):
    return render(request, 'analysis_home.html', {})


def analysis_multisearch(request):
    return render(request, 'analysis_multisearch.html', {})


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
        # Speed up queries.
        # TODO: how can we make this more faster/effective with less queries.  
        genes = genes.prefetch_related('dataset', 'homologenes', 'dataset__publication').all()
        total_results = len(genes)
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
