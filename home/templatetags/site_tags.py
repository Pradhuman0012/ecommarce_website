
import datetime
from django import template
register = template.Library()

from django.db.models import Count



@register.simple_tag
def current_time(format_string):
    return datetime.datetime.now().strftime(format_string)