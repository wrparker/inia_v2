from django import template
from django.utils.safestring import mark_safe
from inia.analysis.search import LegacyAPIHelper

register = template.Library()

@register.simple_tag(name='get_abbreviations')
def get_abbreviations(brain_regions):
    return mark_safe(', '.join(['<strong>{}</strong>:{}'.format(i.abbreviation, i.name) for i in brain_regions]))

@register.simple_tag(name='direction_tooltip')
def regulation_tooltip(direction):
    if direction.lower() == 'down':
        return mark_safe("<td id='tooltip' rel='tooltip' data-placement='left' data-original-title='<strong>Direction: DOWN</strong><br />Downregulated in alcohol-preferring animals, human alcoholics, or after alcohol'>"+direction+"</td>")
    elif direction.lower() == 'up':
        return mark_safe("<td id='tooltip' rel='tooltip' data-placement='left' data-original-title='<strong>Direction: UP<br /></strong>Upregulated in alcohol-preferring animals, human alcoholics, or after alcohol.'>"+direction+"</td>")


@register.simple_tag(name='exclude_name_form_checkbox')
def exclude_name_form_checkbox(request):
    input_field = "<input type='checkbox' name='excludeName' {} /> <small>Search Gene Symbols and Unique IDs Only"
    if request.GET.get('excludeName', None):
        return mark_safe(input_field.format('checked'))
    else:
        return mark_safe(input_field.format(''))

@register.simple_tag(name='advanced_gene_search_filters_as_table')
def advanced_gene_search_filters_as_table(request):
    filter_html = ''
    filter_html += '<table>'
    for param in LegacyAPIHelper.ADVANCED_FILTER_OPTIONS:
        options = LegacyAPIHelper.unqiue_values_fn_map(param)()
        param_value = request.GET.get(param, None)
        filter_html += '<tr>'
        filter_html += '<td>'
        filter_html += param.title() + ':</td><td><select id="adv-filter-select" name='+param+'>'
        filter_html += '<option value="">Any</option>'
        for option in options:
            selected = ''
            if param_value and param_value.lower() == option:
                selected = 'selected'
            filter_html += '<option value="{}" {}>{}</option>'.format(option, selected, option.title())
        filter_html += '</select>'
        filter_html += '</td>'
        filter_html += '</tr>'
    filter_html += '</table>'
    return mark_safe(filter_html)

@register.simple_tag(name='advanced_gene_search_filters_as_p')
def advanced_gene_search_filters_as_table(request, html_class=''):
    filter_html = ''
    for param in LegacyAPIHelper.ADVANCED_FILTER_OPTIONS:
        options = LegacyAPIHelper.unqiue_values_fn_map(param)()
        param_value = request.GET.get(param, None)
        filter_html += '<p class={}>'.format(html_class)
        filter_html += param.title() + ':</p><p class={}><select id="adv-filter-select" name='+param+'>'.format(html_class)
        filter_html += '<option value="">Any</option>'
        for option in options:
            selected = ''
            if param_value and param_value.lower() == option:
                selected = 'selected'
            filter_html += '<option value="{}" {}>{}</option>'.format(option, selected, option.title())
        filter_html += '</select>'
        filter_html += '</p>'
    return mark_safe(filter_html)