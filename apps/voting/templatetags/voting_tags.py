from django import template
from apps.voting.utils import encode_id

register = template.Library()

@register.filter
def encoded(value):
    return encode_id(int(value))