from django import template
from apps.voting.utils import encode_id

register = template.Library()

@register.filter
def encoded(value):
    return encode_id(int(value))

@register.filter
def initials(value):
    """Return uppercase initials, skipping filler words.
    e.g. 'Young Professional of the Year' → 'YPY'
         'Career Excellence Award'        → 'CEA'
    """
    SKIP = {'of', 'the', 'a', 'an', 'and', 'or', 'for', 'in', 'on', 'at', 'to', 'by', 'with'}
    words = str(value).split()
    return ''.join(w[0].upper() for w in words if w and w.lower() not in SKIP)