from django import template
from django.utils.safestring import mark_safe
from inia.common import color_variant
from inia.models import BrainRegion, Dataset
from inia.analysis.search import LegacyAPIHelper

register = template.Library()

@register.simple_tag(name='mark_pvalue')
def mark_pvalue(score):
    if float(score) <= 0.05:
        return mark_safe('<mark>{}</mark>'.format(score))
    else:
        return score

@register.simple_tag(name='get_abbreviations')
def get_abbreviations(brain_regions):
    if not brain_regions:
        brain_regions = BrainRegion.objects.all().order_by('name')
    return mark_safe(', '.join(['<strong>{}</strong>:{}'.format(i.abbreviation, i.name) for i in brain_regions]))

@register.simple_tag(name='direction_tooltip')
def regulation_tooltip(direction):
    if direction.lower() == 'down':
        return mark_safe("<td id='tooltip' rel='tooltip' data-placement='left' data-original-title='<strong>Direction: DOWN</strong><br />Downregulated in alcohol-preferring animals, human alcoholics, or after alcohol'>"+direction+"</td>")
    elif direction.lower() == 'up':
        return mark_safe("<td id='tooltip' rel='tooltip' data-placement='left' data-original-title='<strong>Direction: UP<br /></strong>Upregulated in alcohol-preferring animals, human alcoholics, or after alcohol.'>"+direction+"</td>")


@register.simple_tag(name='exclude_name_form_checkbox')
def exclude_name_form_checkbox(request):
    input_field = "<input class='excludeName' type='checkbox' name='excludeName' {} /> <small>Search Gene Symbols and Unique IDs Only"
    if request.GET.get('excludeName', None):
        return mark_safe(input_field.format('checked'))
    else:
        return mark_safe(input_field.format(''))

@register.simple_tag(name='advanced_gene_search_filters_as_table')
def advanced_gene_search_filters_as_table(request):
    filter_html = ''
    filter_html += '<table>'
    for param in LegacyAPIHelper.ADVANCED_FILTER_OPTIONS:
        options = LegacyAPIHelper.unqiue_values_fn_map(param, result_as_lower=False)()
        param_value = request.GET.get(param, None)
        filter_html += '<tr>'
        filter_html += '<td>'
        filter_html += param.title() + ':</td><td><select class="adv-filter-select" name='+param+'>'
        filter_html += '<option value="">Any</option>'
        for option in options:
            selected = ''
            if param_value and param_value.lower() == option.lower():  #redo case because we dont get results as lower
                selected = 'selected'
            filter_html += '<option value="{}" {}>{}</option>'.format(option.lower(), selected, option)
        filter_html += '</select>'
        filter_html += '</td>'
        filter_html += '</tr>'
    filter_html += '</table>'
    return mark_safe(filter_html)

@register.simple_tag(name='gene_network_cytoscape_elements')
def gene_network_cytoscape_elements(graph):
    cytoscape_js = ''
    # step 1: nodes.
    for node in graph['nodes']:
        cytoscape_js += '{data: {id: \''+node['symbol']+'\', num_datasets: \''+str(node['num_datasets'])+'\' }},\n'

    for edge in graph['edges']:
        cytoscape_js += "{data: { id: '"+edge['id'] + "', " \
                        "source: '" + edge['source'] + "', " \
                        "target: '"+edge['destination'] + "', " \
                        "label: '"+edge['label'] + "'," \
                        "num_overlap: '"+str(edge['num_overlap'])+"', }},\n"

    return mark_safe(cytoscape_js)

@register.simple_tag(name='gene_network_cytoscape_edge_width')
def gene_network_cytoscape_edge_width():
    color = '#e8ffff'  # increments of 25.
    cytoscape_js = ''
    num = Dataset.objects.all().count()
    for i in range(num):
        cytoscape_js += '{selector: "edge[num_overlap=\''+str(i)+'\']", style:{width:'+str(i)+'}},\n'
        cytoscape_js += '{selector: "node[num_datasets=\''+str(i)+'\']", style:{\'background-color\':\''+color+'\'}},\n'
        if i < num:
            color = color_variant(color, -5)
    return mark_safe(cytoscape_js)


