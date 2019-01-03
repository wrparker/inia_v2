from django.http import HttpResponse
from urllib.parse import unquote
from django.shortcuts import render
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Publication, Dataset, BrainRegion, IniaGene
from .forms import ContactForm
from .analysis.search import base_gene_search, LegacyAPIHelper

from common import remove_from_url

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

        genes = genes.order_by('gene_symbol') if genes else IniaGene.objects.none()
        total_results = len(genes)
        paginator = Paginator(genes, 100)
        page = request.GET.get('page', 1)
        urlencode = request.GET.urlencode()
        # TODO: need to remove page and output form urlencode... well page for regular stuff and output for csv link
        genes = paginator.get_page(page)
        if output == 'html':
            return render(request, 'search.html', {'genes': genes,
                                                   'urlencode': urlencode,
                                                   'total_results': total_results,
                                                   'errors': errors
                                                   #'old_search': unquote(request.GET.get('gene', None))
                                                   })
    else:
        return render(request, 'search.html', {'errors': errors})
