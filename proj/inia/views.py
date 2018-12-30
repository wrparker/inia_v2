from django.http import HttpResponse

import logging

_LOG = logging.getLogger('application.'+ __name__)

def index(request):
    _LOG.info('hi!')
    return HttpResponse('hello')
