# documentos/templatetags/extras.py
from django import template
register = template.Library()

@register.filter
def add_attribute(field, attr):
    param, val = attr.split(':',1)
    return field.as_widget(attrs={param: val})
