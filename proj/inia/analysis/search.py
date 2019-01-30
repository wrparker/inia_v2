import re
from django.db.models import Q
from django.db.models.functions import Lower
from django.utils.html import strip_tags
from inia.models import IniaGene, Dataset, BrainRegion, Publication


_WEBAPP_REGEX_SYMBOLS = {'*': '.*', # matches zero or more characters
                         '~': '.', # matches exactly one character
                         '?': '.?', # matches one or zero characters
                         '^': '^', # matches the beginning of the result
                         '$': "$"  # matches the end of the result
                         # Additionally exact matches are with 'term' or "term"
                         }

# TODO: fix ordering, refactor to make nicer... results are correct though.
def base_gene_search(search, exclude_name=False):
    '''
    This is the primary search function for the web application.  It uses custom regex that was designed in the past.
    Here we conver the regex according to the documentation rules.

    :param search: Non-html encoded string.
    :param exclude_name: if this is true, then we only search gene symbols and UniqueIDs
    :return:
    '''
    search = strip_tags(search)
    search_term_regex = "[^\\s\"']+|\"[^\"]*\"|'[^']*'"  # seaprate
    search_terms = [i.strip() for i in re.findall(search_term_regex, search)]
    search_terms = list(filter(None, search_terms))  # Remove blank strings.
    search_terms = [term.replace('"', "'") for term in search_terms]  # use single quote for all exacts for downstream simplicity

    # Lets build the query.
    results = IniaGene.objects.none()
    for term in search_terms:
        # Exact Matches
        if "'" in term:
            term = term.strip("'")
            if term.isdigit():
                results = results | IniaGene.objects.filter(
                    Q(ncbi_uid=term) |
                    Q(homologenes__homologene_group_id=term)
                )
            #regex exact match:
            elif bool(set(_WEBAPP_REGEX_SYMBOLS.keys() & [c for c in term])):
                for regex_conversion in _WEBAPP_REGEX_SYMBOLS.keys():
                    term = term.replace(regex_conversion, _WEBAPP_REGEX_SYMBOLS[regex_conversion])
                results = results | IniaGene.objects.filter(
                    Q(probe_id__iregex=term) |
                    Q(gene_symbol__iregex=term) |
                    Q(homologenes__gene_symbol__iregex=term) |
                    Q(genealiases__symbol__iregex=term)
                )
                if not exclude_name:
                    results = results | IniaGene.objects.filter(Q(gene_name__iregex='.*' + term + '.*'))
            else:
                results = results | IniaGene.objects.filter(
                    Q(probe_id__iexact=term) |
                    Q(gene_symbol__iexact=term) |
                    Q(homologenes__gene_symbol__iexact=term) |
                    Q(genealiases__symbol__iexact=term)
                )
                if not exclude_name:
                    results = results | IniaGene.objects.filter(Q(gene_name__icontains=term))
        # Regex Matches...
        elif bool(set(_WEBAPP_REGEX_SYMBOLS.keys() & [c for c in term])):  # Assume numbers are not keys bc regex.
            for regex_conversion in _WEBAPP_REGEX_SYMBOLS.keys():
                term = term.replace(regex_conversion, _WEBAPP_REGEX_SYMBOLS[regex_conversion])
            results = results | IniaGene.objects.filter(
                Q(probe_id__iregex=term) |
                Q(gene_symbol__iregex=term) |
                Q(homologenes__gene_symbol__iregex=term) |
                Q(genealiases__symbol__iregex=term)
            )
            if not exclude_name:
                results = results | IniaGene.objects.filter(Q(gene_name__iregex='.*' + term + '.*'))

        # Plain matches (basically *term*).
        else:
            if term.isdigit():
                results = results | IniaGene.objects.filter(
                    Q(ncbi_uid=term) |
                    Q(homologenes__homologene_group_id=term)
                )
            else:
                results = results | IniaGene.objects.filter(
                    Q(probe_id__icontains=term) |
                    Q(gene_symbol__icontains=term) |
                    Q(homologenes__gene_symbol__icontains=term) |
                    Q(genealiases__symbol__icontains=term)
                )
                if not exclude_name:
                    results = results | IniaGene.objects.filter(Q(gene_name__icontains=term))

    results = results.distinct()
    return results


class LegacyAPIHelper:
    ALLOWED_API_PARAMETERS = [
        'output', # NON ADV FILTER VAL
        'gene',   # NON ADV FILTER VAL
        'page',   # NON ADV FILTER VAL allowed for pagination
        'excludeName',# NON ADV FILTER VAL
        'direction',
        'alcohol',
        'microarray',
        'model',
        'phenotype',
        'species',
        'region',
        'paradigm',
        'publication',
        'dataset'
    ]
    ADVANCED_FILTER_OPTIONS = ALLOWED_API_PARAMETERS[4:]  # just slice above array
    @staticmethod
    def check_and_return_valid_values(api_parameter, api_value):
        unique_values = LegacyAPIHelper.unqiue_values_fn_map(api_parameter)()
        if api_value.lower() in unique_values:
            return True, unique_values
        else:
            return False, unique_values
    @staticmethod
    def perform_filter(api_parameter, queryset, api_value):
        return LegacyAPIHelper.filter_fn_map(api_parameter, queryset)(api_value)

    @staticmethod
    def filter_fn_map(api_param, iniagene_queryset):
        def get_microarray(needle):
            return iniagene_queryset.filter(dataset__microarray__iexact=needle)

        def get_alcohol(needle):
            needle = needle.lower() in ['true', 'yes', '1']
            return iniagene_queryset.filter(dataset__alcohol=needle)

        def get_direction(needle):
            return iniagene_queryset.filter(direction__iexact=needle)

        def get_model(needle):
            return iniagene_queryset.filter(dataset__model__iexact=needle)

        def get_phenotype(needle):
            return iniagene_queryset.filter(dataset__phenotype__iexact=needle)

        def get_species(needle):
            return iniagene_queryset.filter(dataset__species__iexact=needle)

        def get_brain_region(needle):
            region = BrainRegion.objects.get(Q(name__iexact=needle) | Q(abbreviation__iexact=needle))
            if region.is_super_group:
                return iniagene_queryset.filter(Q(dataset__brain_region=region) |
                                                Q(dataset__brain_region__in=region.sub_groups.all()))
            else:
                return iniagene_queryset.filter(Q(dataset__brain_region=region))

        def get_paradigm(needle):
            return iniagene_queryset.filter(dataset__paradigm__iexact=needle)

        def get_publication(needle):
            return iniagene_queryset.filter(dataset__publication__htmlid__iexact=needle)

        def get_dataset(needle):
            return iniagene_queryset.filter(dataset__name__iexact=needle)

        filter_map = {
            'microarray': get_microarray,
            'alcohol': get_alcohol,
            'direction': get_direction,
            'model': get_model,
            'phenotype': get_phenotype,
            'species': get_species,
            'region': get_brain_region,
            'paradigm': get_paradigm,
            'publication': get_publication,
            'dataset': get_dataset,
        }
        return filter_map[api_param]

    @staticmethod
    def unqiue_values_fn_map(value, result_as_lower=True):
        def get_microarray():
            return [choice[0].lower() if result_as_lower else choice[0] for choice in Dataset.objects.values_list('microarray').distinct()]

        def get_alcohol():
            return ['yes', 'no']

        def get_direction():
            return [choice[0].lower() if result_as_lower else choice[0] for choice in IniaGene.DIRECTION_CHOICES]

        def get_model():
            return [choice[0].lower() if result_as_lower else choice[0] for choice in Dataset.objects.values_list('model').distinct()]

        def get_phenotype():
            return [choice[0].lower() if result_as_lower else choice[0] for choice in Dataset.objects.values_list('phenotype').distinct()]

        def get_species():
            return [choice[0].lower() if result_as_lower else choice[0] for choice in Dataset.objects.values_list('species').distinct()]

        def get_brain_region():
            allowed = [choice[0].lower() if result_as_lower else choice[0] for choice in BrainRegion.objects.values_list('name').distinct()]
            allowed.extend([choice[0].lower() if result_as_lower else choice[0] for choice in BrainRegion.objects.values_list('abbreviation').distinct()])
            return allowed

        def get_paradigm():
            return [choice[0].lower() if result_as_lower else choice[0] for choice in Dataset.objects.values_list('paradigm').distinct()]

        def get_publication():
            return [choice[0].lower() if result_as_lower else choice[0] for choice in Publication.objects.values_list('htmlid').distinct()]

        def get_dataset():
            return [choice[0].lower() if result_as_lower else choice[0] for choice in Dataset.objects.values_list('name').distinct()]
        unique_values = {
            'microarray': get_microarray,
            'alcohol': get_alcohol,
            'direction': get_direction,
            'model': get_model,
            'phenotype': get_phenotype,
            'species': get_species,
            'region': get_brain_region,
            'paradigm': get_paradigm,
            'publication': get_publication,
            'dataset': get_dataset,
        }
        return unique_values[value]





