from django.http import HttpResponse
from django.shortcuts import render
from .models import Publication, Dataset, BrainRegion
from .forms import ContactForm

import logging

_LOG = logging.getLogger('application.'+ __name__)


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
        info_by_region[region.name]['datasets'] = list(region.dataset_set.all().order_by('official_dataset_name'))
        info_by_region[region.name]['total'] = 0
        for ds in info_by_region[region.name]['datasets']:
            info_by_region[region.name]['total'] += ds.get_number_genes()
    return render(request, 'datasets.html', {'publications': publications,
                                             'info_by_region': info_by_region,
                                             'brain_regions': brain_regions})
