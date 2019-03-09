from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
import logging
import traceback
from inia.models import Dataset
from inia.analysis.intersect import hypergeometric_score
from itertools import combinations

_LOG = logging.getLogger('application.'+__name__)

class Command(BaseCommand):
    help = 'Uses the database to make ane export of the latest autocompletes.'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        '''
        This command should generate a parital view for the existing datasets by calculating the theoretical intersections
        between each set.  We cache this information rather than run it every time the page is loaded because it
        can take quite a bit of database load.

        O(n) = N^2

        User generated datasets are then just utilized on an as-needed basis.
        '''
    try:
        data_sets = Dataset.objects.all().prefetch_related('iniagene_set').order_by('name')[:4]
        combinations = combinations(data_sets, 2)
        #cc = []
        #for combination in combinations:
        #    cc.append(hypergeometric_score(combination[0], combination[1]))
        html = '<tr>'
        # header
        for ds in data_sets:
            html += '<td class="col-name">'
            html += ds.name
            html += '</td>'
        html += '</tr>'

        # Data...
        for ds in data_sets:
            html += '<tr>'
            html += '<td>'
            html += ds.name
            html += '</td>'
        # maybe can't utilize combinatinos... since we need table output... investigate further.
            for ds2 in data_sets:
                html +=


    except:
        _LOG.error("Exception:")
        _LOG.error(traceback.format_exc())
