from django import template
from django.utils.safestring import mark_safe
from inia.models import BrainRegion


register = template.Library()

@register.simple_tag(name='get_abbreviations')
def get_abbreviations(brain_regions):
    return mark_safe(', '.join(['<strong>{}</strong>:{}'.format(i.abbreviation, i.name) for i in brain_regions]))
