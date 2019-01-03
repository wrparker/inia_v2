from django.http import HttpResponse
from urllib.parse import unquote
from django.shortcuts import render
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Publication, Dataset, BrainRegion, IniaGene
from .forms import ContactForm
from .analysis.search import base_gene_search

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
    ''' Regex Values are allowed... separated by pipe?'''
    result = {}
    output = request.GET.get('output', '')
    api_parameters = ['output',
                      'gene',
                      'direction',
                      'excludeName',
                      'alcohol',
                      'microarray',
                      'model',
                      'phenotype',
                      'species',
                      'region',
                      'paradigm',
                      'publication',
                      'page' #allowed for pagination
                       ]
    _err_msg = 'Unexpected input for {}. You gave {}. ALLOWED: {}'
    _allowed_boolean_values = ['true', 'false', 'no', 'yes', '1', '0']
    _true_boolean_values = ['true', 'yes', '1']

    for param in request.GET:
        if param not in api_parameters:
            return render(request, 'search.html', {'error': 'Unexpected parameter given: {}'.format(param)})

    gene_param = request.GET.get('gene', None)
    if gene_param:
        gene_param = unquote(gene_param)
        genes = base_gene_search(gene_param, exclude_name=request.GET.get('excludeName', False))
    else:
        # is there a param?
        genes = False
        for param in api_parameters:
            if request.GET.get(param, None):
                genes = True
        if genes:
            genes = IniaGene.objects.all()
    if genes:
        # Microarray filter
        microarray = request.GET.get('microarray', None)
        if microarray:
            microarray = unquote(microarray.lower())
            allowed_choices = [choice[0].lower() for choice in Dataset.objects.values_list('microarray').distinct()]
            if microarray in allowed_choices:
                genes = genes.filter(dataset__microarray__iexact=microarray)
            else:
                return render(request, 'search.html',
                              {'error': _err_msg.format('microarray', microarray,
                                                        ', '.join(i.title() for i in allowed_choices))})
        # Alcohol filter
        alcohol = (request.GET.get('alcohol', None))
        if alcohol:
            alcohol = unquote(alcohol.lower())
            allowed_choices = _allowed_boolean_values
            # Accept True/False/No/Yes otherwise Error
            if alcohol in allowed_choices:
                alcohol = alcohol in _true_boolean_values # get bool
                genes = genes.filter(dataset__alcohol=alcohol)
            else:
                return render(request, 'search.html',
                       {'error': _err_msg.format('alcohol', alcohol, ', '.join(allowed_choices))})

        # Direction Filter
        direction = request.GET.get('direction', None)
        if direction:
            direction = unquote(direction.lower())
            allowed_choices = [choice[0].lower() for choice in IniaGene.DIRECTION_CHOICES]
            if direction in allowed_choices:
                genes = genes.filter(direction__iexact=direction)
            else:
                return render(request, 'search.html',
                              {'error': _err_msg.format('direction', direction, ', '.join(i for i in allowed_choices))})
        # Model Filter
        model = request.GET.get('model', None)
        if model:
            model = unquote(model.lower())
            allowed_choices = [choice[0].lower() for choice in Dataset.objects.values_list('model').distinct()]
            if model in allowed_choices:
                genes = genes.filter(dataset__model=model)
            else:
                return render(request, 'search.html',
                              {'error': _err_msg.format('model', model, ', '.join(i for i in allowed_choices))})

        # phenotype filter
        phenotype = request.GET.get('phenotype', None)
        if phenotype:
            phenotype = unquote(phenotype.lower())
            allowed_choices = [choice[0].lower() for choice in Dataset.objects.values_list('phenotype').distinct()]
            if phenotype in allowed_choices:
                genes = genes.filter(dataset__phenotype=phenotype)
            else:
                return render(request, 'search.html',
                              {'error': _err_msg.format('phenotype', phenotype, ', '.join(i for i in allowed_choices))})

        # species filter
        species = request.GET.get('species', None)
        if species:
            species = unquote(species.lower())
            allowed_choices = [choice[0].lower() for choice in Dataset.objects.values_list('species').distinct()]
            if species in allowed_choices:
                genes = genes.filter(dataset__species=species)
            else:
                return render(request, 'search.html',
                              {'error': _err_msg.format('species', species, ', '.join(i for i in allowed_choices))})

        # brain_region filter
        brain_region = request.GET.get('region', None)
        if brain_region:
            brain_region = unquote(brain_region.lower())
            allowed_choices = [choice[0].lower() for choice in BrainRegion.objects.values_list('name').distinct()]
            allowed_choices.extend([choice[0].lower() for choice in BrainRegion.objects.values_list('abbreviation').distinct()])
            if brain_region in allowed_choices:
                br = BrainRegion.objects.get(Q(name=brain_region)| Q(abbreviation=brain_region))
                if br.is_super_group:
                    genes = genes.filter(Q(dataset__brain_region=br) | Q(dataset__brain_region__in=br.sub_groups.all()))
                else:
                    genes = genes.filter(dataset__brain_region=br)

            else:
                return render(request, 'search.html',
                              {'error': _err_msg.format('brain_region', brain_region,
                                                        ', '.join(i for i in allowed_choices))})
        #Alcohol Paradigm filter
        paradigm = request.GET.get('paradigm', None)
        if paradigm:
            paradigm = unquote(paradigm.lower())
            allowed_choices = [choice[0].lower() for choice in Dataset.objects.values_list('paradigm').distinct()]
            if paradigm in allowed_choices:
                genes = genes.filter(dataset__paradigm__iexact=paradigm)
            else:
                return render(request, 'search.html',
                              {'error': _err_msg.format('paradigm', paradigm, ', '.join(i for i in allowed_choices))})

        #publication filter
        publication = request.GET.get('publication', None)
        if publication:
            publication = unquote(publication.lower())
            allowed_choices = [choice[0].lower() for choice in Publication.objects.values_list('htmlid').distinct()]
            if publication in allowed_choices:
                genes = genes.filter(dataset__publication__htmlid__iexact=publication)
            else:
                return render(request, 'search.html',
                              {'error': _err_msg.format('publication', publication, ', '.join(i for i in allowed_choices))})

        #Datset Filter
        dataset = request.GET.get('dataset', None)
        if dataset:
            dataset = unquote(dataset.lower())
            allowed_choices = [choice[0].lower() for choice in Dataset.objects.values_list('name').distinct()]
            if dataset in allowed_choices:
                genes = genes.filter(dataset__name=dataset)
            else:
                return render(request, 'search.html',
                              {'error': _err_msg.format('dataset', dataset, ', '.join(i for i in allowed_choices))})
        total_results = len(genes)
        paginator = Paginator(genes, 100)
        page = request.GET.get('page', 1)
        urlencode = request.GET.urlencode().replace('page='+str(page), '')
        genes = paginator.get_page(page)
        return render(request, 'search.html', {'genes': genes,
                                               'urlencode': urlencode,
                                               'total_results': total_results})




    else:
        return render(request, 'search.html', {'error':'No query given.'})

