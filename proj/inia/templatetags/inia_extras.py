from django import template
from django.utils.safestring import mark_safe
from inia.models import BrainRegion


register = template.Library()

@register.simple_tag(name='get_abbreviations')
def get_abbreviations(brain_regions):
    return mark_safe(', '.join(['<strong>{}</strong>:{}'.format(i.abbreviation, i.name) for i in brain_regions]))

@register.simple_tag(name='direction_tooltip')
def regulation_tooltip(direction):
    if direction.lower() == 'down':
        return mark_safe("<div style='text-decoration:underline;' rel='tooltip' data-original-title='<strong>Direction: DOWN</strong><br />Downregulated in alcohol-preferring animals, human alcoholics, or after alcohol'>"+direction+"</div>")
    elif direction.lower() == 'up':
        return mark_safe("<div style='text-decoration:underline;' rel='tooltip' data-original-title='<strong>Direction: UP<br /></strong>Upregulated in alcohol-preferring animals, human alcoholics, or after alcohol.'>"+direction+"</div>")
