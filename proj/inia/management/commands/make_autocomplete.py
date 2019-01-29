from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
import logging
import traceback
from inia.models import IniaGene

_LOG = logging.getLogger('application.'+__name__)

class Command(BaseCommand):
    help = 'Uses the database to make ane export of the latest autocompletes.'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        '''
        This command should not be run, but not removing code for it incase it is needed in the future.  For now the
        command will exit if called to prevent accidenal calling.
        '''
    try:
        _LOG.info("generating autocomplete js...")
        genes = IniaGene.objects.filter(Q(gene_symbol__isnull=False)).exclude(gene_symbol__exact='')
        symbols = genes.values_list('gene_symbol')

        symbols = set([i[0] for i in symbols])

        with open('proj/static/js/search_autocomplete.js', 'w') as f:
            f.write('var genes = [')
            for sym in symbols:
                f.write('"{}",'.format(sym))
            f.write('];')

            f.write("$('.gene-query').autocomplete({source: genes});")

    except:
        _LOG.error("Exception:")
        _LOG.error(traceback.format_exc())
