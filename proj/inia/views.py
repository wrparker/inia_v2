from django.http import HttpResponse
from django.shortcuts import render
from .models import Publication

import logging

_LOG = logging.getLogger('application.'+ __name__)

def index(request):
    return render(request, 'home.html', {})

def analysis_home(request):
    return render(request, 'analysis_home.html', {})

def datasets(request):
    publications = Publication.objects.all()
    return render(request, 'datasets.html', {'publications': publications})
