from django.http import HttpResponse
from django.shortcuts import render

import logging

_LOG = logging.getLogger('application.'+ __name__)

def index(request):
    _LOG.info('hi!')
    return render(request, 'home.html', {'test_var': 'test'})
