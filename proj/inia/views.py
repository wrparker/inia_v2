import tempfile
import csv
from django.http import HttpResponse
from urllib.parse import unquote, parse_qs, urlencode
from django.shortcuts import render, redirect
from django.db.models import F, Q
from django.core.paginator import Paginator
from .models import Publication, Dataset, BrainRegion, IniaGene, SpeciesType, SavedSearch
from .forms import ContactForm
from .analysis.search import base_gene_search, LegacyAPIHelper
from .analysis.intersect import hypergeometric_score, format_hypergeometric_score, custom_dataset_intersection
from .analysis.multisearch import multisearch_results
from .common import open_tmp_search, dict_list_to_csv, color_variant
from functools import reduce
from itertools import combinations

import logging

_LOG = logging.getLogger('application.'+ __name__)

_ALLOWED_TRUE_BOOLEANS = ['yes', '1', 'true']


def index(request):
    return render(request, 'home.html', {})


def analysis_home(request):
    return render(request, 'analysis_home.html', {})


def analysis_multisearch(request):
    genes, result_table, inputs, not_found = '', [], {}, None
    if request.method == 'GET':
        id = request.GET.get('id')
        # Load in search inputs
        if id:
            inputs = open_tmp_search(id)
            result_table, not_found = multisearch_results(inputs['genes'],
                                                          species=inputs['species'],
                                                          return_not_found=True)

    elif request.method == "POST":
        analysis_type = request.POST.get('type')
        # No id have to do some crappy delimiting here.
        genes = request.POST.get('allgenes')
        genes = genes.replace('\r\n', ',').replace('\n', ',').replace('\r', ',').replace('|', ',').replace('+',',')
        genes = [g.strip() for g in genes.split(',') if g.strip()]

        if request.POST.get('species') == 'mouse':
            species = SpeciesType.MUS_MUSCULUS
        elif request.POST.get('species') == 'rat':
            species = SpeciesType.RATTUS_NORVEGICUS
        else:
            species = SpeciesType.HOMO_SAPIENS

        # only store actual input.
        if genes:
            dataset_title = request.POST.get('title')

            # Store input sin a temporary file...? Maybe move this out to db?
            inputs = {'species': species,
                      'genes': genes,
                      'title': dataset_title
                      }
            search = SavedSearch.objects.create(search_parameters=inputs)
            inputs['id'] = search.id

        # Don't ever do anything wiht post, just return redirect.
        # add url to self...
        id = urlencode({'id': inputs['id']})
        if analysis_type == 'multisearch':
            return redirect(request.path_info+'?'+id)

        elif analysis_type == 'network':
            pass
        elif analysis_type == 'dataset':
            pass
        else:
            pass
        # create file for data
    return render(request, 'analysis_multisearch.html', {'result_table': result_table, 'inputs': inputs,
                                                         'not_found': not_found})


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


# TODO: This should ideally be refactored out into a proper API, but we need to provide legacy support...
# TODO: This is kind of ugly as is...
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

        genes = genes.order_by(F('gene_symbol').asc(nulls_last=True)) if genes else IniaGene.objects.none()
        genes = genes.prefetch_related('dataset', 'homologenes', 'dataset__publication', 'genealiases_set', 'dataset__brain_regions').all()
        total_results = genes.count()
        if output == 'html':
            # Only paginate HTML format.
            paginator = Paginator(genes, 100)
            page = request.GET.get('page', 1)
            query = request.GET.urlencode()
            query = parse_qs(query)
            query.pop('page', None)
            query.pop('output', None)
            query = urlencode(query, doseq=True)
            genes = paginator.get_page(page)
            return render(request, 'search.html', {'genes': genes,
                                                   'urlencode': query,
                                                   'total_results': total_results,
                                                   'errors': errors
                                                   })
        else:  #if we don't recognize 'html' or whatever we just make it a csv, return the file.
            # convert to dict...
            output = []
            for gene in genes:
                gene_info = {}
                gene_info['NCBI UID'] = gene.ncbi_uid
                gene_info['Gene Symbol'] = gene.ncbi_uid
                gene_info['Gene Name'] = gene.ncbi_uid
                gene_info['aliases'] = ', '.join(gene.genealiases_set.all().values_list('symbol', flat=True))
                gene_info['Homologene Id'] = gene.get_homologene_id()
                gene_info['Human Orthologs'] = gene.list_human_orthologs()
                gene_info['Rat Orthologs'] = gene.list_rat_orthologs()
                gene_info['Mouse Orthologs'] = gene.list_mouse_orthologs()
                gene_info['Gene Expression Platform'] = gene.dataset.microarray
                gene_info['Probe Id'] = gene.probe_id
                gene_info['Species'] = gene.dataset.species
                gene_info['Ethanol/Treatment'] = gene.dataset.treatment
                gene_info['Brain region/Cell type'] = ','.join([f.name for f in gene.dataset.brain_regions.all()])
                gene_info['P-value'] = gene.p_value
                gene_info['Direction of Change'] = gene.direction
                gene_info['Est FDR'] = gene.fdr
                gene_info['Dataset'] = gene.dataset.name
                gene_info['Reference'] = gene.dataset.publication.get_short_name()
                output.append(gene_info)
            result_file = dict_list_to_csv(output)
            response = HttpResponse(content=open(result_file, 'rb'))
            response['Content-Type'] = 'text'
            response['Content-Disposition'] = 'attachment; filename="results.csv"'
            return response
    else:
        return render(request, 'search.html', {'errors': errors})


def boolean_dataset(request):
    # TODO: dataset comprised of the smaller (fer2017, etc...)
    # TODO: This should probably be refactored out into something more concise.
    selected_ds = [ds for ds in request.GET.getlist('ds') if ds != '']
    selected_br = [br for br in request.GET.getlist('br') if br != '']
    if not request.GET.get('operation') or not selected_ds or len(selected_ds) <= 1:
        brain_regions = BrainRegion.objects.all().order_by('name')
        publications = Publication.objects.all().order_by('-date_sub').prefetch_related('dataset_set')
        return render(request, 'boolean_dataset.html', {'brain_regions': brain_regions,
                                                        'publications': publications})
    else:
        data_sets = Dataset.objects.filter(pk__in=selected_ds).prefetch_related('iniagene_set')
        brain_regions = [BrainRegion.objects.get(pk=br) for br in selected_br]
        brain_region_names = ', '.join([br.name for br in brain_regions])
        dataset_names = ', '.join([ds.name for ds in data_sets])
        operation = request.GET.get('operation')

        if operation:
            qs = []
            allowed_result = []
            for ds in data_sets:
                homologenes = set(ds.iniagene_set.exclude(homologenes=None).values_list('homologenes__homologene_group_id', flat=True))
                if not allowed_result:  #  initialize it.
                    allowed_result.extend(homologenes)
                    allowed_result = set(allowed_result)
                else:
                    if operation == 'intersect':
                        allowed_result &= homologenes
                    elif operation == 'union':
                        allowed_result |= homologenes
                    if not allowed_result:
                        return render(request, 'boolean_dataset.html', {'results': {},
                                                                        'dataset_names': dataset_names,
                                                                        'brain_region_names': brain_region_names,
                                                                        'intersection_species': 'None'})

            d_list = map(lambda n: Q(dataset=n), data_sets)
            d_list = reduce(lambda a, b: a | b, d_list)

            h_list = map(lambda n: Q(homologenes__homologene_group_id=str(n)), list(allowed_result))
            h_list = reduce(lambda a, b: a | b, h_list)

            if selected_br:
                br_list = map(lambda n: Q(dataset__brain_regions=n), brain_regions)
                br_list = reduce(lambda a, b: a | b, br_list)

            if not selected_br:
                genes = IniaGene.objects.filter(Q(h_list) & Q(d_list)).prefetch_related('homologenes', 'dataset')
            else:
                genes = IniaGene.objects.filter(Q(h_list) & Q(d_list) & Q(br_list)).prefetch_related('homologenes', 'dataset')

            if not genes:   # br filter caused no genes.
                return render(request, 'boolean_dataset.html', {'results': {},
                                                                'dataset_names': dataset_names,
                                                                'brain_region_names': brain_region_names,
                                                                'intersection_species': 'None'})

            intersection_species = None

            if len(set(genes.values_list('dataset__species', flat=True))) > 1:
                intersection_species = 'mixed species'
            else:
                intersection_species = genes[0].dataset.species + ' only'


            tmp = {}
            # Sort into a dictionary with homologene-id as key.
            for gene in genes:
                hgene_group_id = gene.get_homologene_id()
                if not hgene_group_id:
                    if not tmp.get(gene.probe_id): # use probe id since we don't have homologene...
                        tmp[gene.probe_id] = []
                    tmp[gene.probe_id].append(gene)
                else:
                    if not tmp.get(hgene_group_id):
                        tmp[hgene_group_id] = []
                    tmp[hgene_group_id].append(gene)

            results = []
            for h_id, genes in tmp.items():  # Result row.
                row = {}
                # Use first element to get the universal information...

                row['human'] = genes[0].list_human_orthologs()
                row['mouse'] = genes[0].list_mouse_orthologs()
                row['rat'] = genes[0].list_rat_orthologs()
                row['homologene_id'] = h_id

                if operation == 'intersect':
                    # direction per dataset:
                    ds_directions = {}
                    for gene in genes:
                        if not ds_directions.get(gene.dataset.name):
                            ds_directions[gene.dataset.name] = gene.direction
                        elif ds_directions[gene.dataset.name] != gene.direction:
                            ds_directions[gene.dataset.name] = 'BOTH'
                    directions = [direction for dataset, direction in ds_directions.items()]

                    row['directions_per_dataset'] = ', '.join(directions)
                    if len(set(directions)) > 1:
                        row['overall_direction'] = 'DIFF'
                    else:
                        row['overall_direction'] = 'SAME'

                elif operation == 'union':  # pubs per item
                    row['datasets'] = ', '.join(set([gene.dataset.name for gene in genes]))

                results.append(row)

            results = sorted(results, key=lambda k: k['human'])  # Sort by human key.

            if(request.GET.get('output') == 'csv'):
                result_file = dict_list_to_csv(results)
                response = HttpResponse(content=open(result_file, 'rb'))
                response['Content-Type'] = 'text'
                response['Content-Disposition'] = 'attachment; filename="results.csv"'
                return response

            csv_url = request.GET.urlencode()
            csv_url = parse_qs(csv_url)
            csv_url['output'] = 'csv'
            csv_url = urlencode(csv_url, doseq=True)

            # Stats table:
            if operation == 'intersect' and data_sets.count() == 2:
                intersection_stats = hypergeometric_score(data_sets[0],
                                                          data_sets[1],
                                                          num_overlap=len(results),
                                                          return_params_as_dict=True)
                intersection_stats['hypergeometric_score'] = format_hypergeometric_score(intersection_stats['hypergeometric_score'])
            return render(request, 'boolean_dataset.html', {'results': results,
                                                            'dataset_names': dataset_names,
                                                            'brain_region_names': brain_region_names,
                                                            'intersection_species': intersection_species,
                                                            'intersection_stats': intersection_stats,
                                                            'csv_url': csv_url})
def dataset_network(request):
    inputs = {}
    brain_regions = BrainRegion.objects.all().order_by('name')
    if request.GET.get('id'):
        # TODO: Some duplicated code here...
        data_sets = Dataset.objects.all().order_by('name').prefetch_related('iniagene_set')
        inputs = open_tmp_search(request.GET.get('id'))
        genes = multisearch_results(inputs['genes'], species=inputs['species'])
        # order same way in generate_dataset_matrix to make table match up...
        inputs['bonferonni'] = []
        for ds in data_sets:
            score = custom_dataset_intersection(genes, inputs['species'], ds)['bonferroni']
            score = format_hypergeometric_score(score)
            inputs['bonferonni'].append(score)

    return render(request, 'dataset_network.html', {'brain_regions': brain_regions,
                                                    'inputs': inputs})
def gene_network(request):
    if not request.GET.get('id'):
        return redirect('inia:analysis_multisearch')
    else:
        # TODO: do we strip ' *' from the name?
        # ex: mouse dglucy
        starting_color = '#e8ffff'  # increments of 50.
        inputs = open_tmp_search(request.GET.get('id'))
        genes = multisearch_results(inputs['genes'], species=inputs['species'])
        graph = {}
        graph['nodes'] = [{'symbol': gene[inputs['species']], 'num_datasets': len(gene['datasets'])} for gene in genes]
        graph['edges'] = []
        for combo in combinations(genes, 2):
            edge = {}
            overlapping_datasets = list(set(combo[0]['datasets']) & set(combo[1]['datasets']))
            edge['num_overlap'] = len(overlapping_datasets)
            if edge['num_overlap'] > 1:
                edge['label'] = ', '.join([o.name for o in overlapping_datasets])
                edge['source'] = combo[0][inputs['species']]
                edge['destination'] = combo[1][inputs['species']]
                edge['id'] = '{}-{}'.format(edge['source'], edge['destination'])
                graph['edges'].append(edge)
    return render(request, 'gene_network.html', {'graph': graph,
                                                 'inputs':inputs})

def overrepresentation_analysis(request):
    inputs = {}
    result_table = []
    if request.GET.get('id'):
        inputs = open_tmp_search(request.GET.get('id'))
        genes  = multisearch_results(inputs['genes'], species=inputs['species'])

        data_sets = Dataset.objects.all().order_by('name')
        inputs['custom_dataset_length'] = len([gene for gene in genes if gene.get('homologene_id')])

        for ds in data_sets:
            row = {}
            intersect_result = custom_dataset_intersection(genes, inputs['species'], ds)
            row['IT_GED_dataset'] = ds.name
            row['hypergeometric_score'] = format_hypergeometric_score(intersect_result['hypergeometric_score'])
            row['adjusted_score'] = intersect_result['bonferroni']
            row['num_overlapping_genes'] = intersect_result['overlap']
            row['adjusted_itged_dataset_size'] = intersect_result['standard_dataset_length']
            row['adjusted_custom_dataset_size'] = intersect_result['custom_dataset_length']
            row['background_size'] = intersect_result['background_homologenes']
            result_table.append(row)
        if request.GET.get('output') == 'csv':
            result_file = dict_list_to_csv(result_table)
            response = HttpResponse(content=open(result_file, 'rb'))
            response['Content-Type'] = 'text'
            response['Content-Disposition'] = 'attachment; filename="results.csv"'
            return response
    else:
        return redirect('inia:analysis_multisearch')

    result_table = sorted(result_table, key=lambda k: k['adjusted_score'])
    for result in result_table:
        result['adjusted_score'] = format_hypergeometric_score(result['adjusted_score'])
    return render(request, 'overrepresentation_analysis.html', {'inputs': inputs, 'result_table': result_table})


