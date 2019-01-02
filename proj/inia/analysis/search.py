import re
from django.db.models import Q
from django.db.models.functions import Lower
from django.utils.html import strip_tags
from inia.models import IniaGene


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
                    Q(uniqueID=term) |
                    Q(homologenes__homologene_group_id=term)
                )
            else:
                results = results | IniaGene.objects.filter(
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
                Q(gene_symbol__iregex=term) |
                Q(homologenes__gene_symbol__iregex=term) |
                Q(genealiases__symbol__iregex=term)
            )
        # Plain matches (basically *term*).
        else:
            if term.isdigit():
                results = results | IniaGene.objects.filter(
                    Q(uniqueID=term) |
                    Q(homologenes__homologene_group_id=term)
                )
            else:
                results = results | IniaGene.objects.filter(
                    Q(gene_symbol__icontains=term) |
                    Q(homologenes__gene_symbol__icontains=term) |
                    Q(genealiases__symbol__icontains=term)
                )
            if not exclude_name:
                results = results | IniaGene.objects.filter(Q(gene_name__icontains=term))

    results = results.distinct()
    return results
