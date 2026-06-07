from django import template
from apps.voting.utils import encode_id

register = template.Library()

@register.filter
def encoded(value):
    return encode_id(int(value))

@register.filter
def initials(value):
    """Return uppercase initials from a string. e.g. 'Career Excellence Award' → 'CEA'"""
    words = str(value).split()
    return ''.join(w[0].upper() for w in words if w)