from home.models import Book_record
import datetime
from django import template
register = template.Library()

from django.db.models import Count
@register.simple_tag
def most_reviewed_book():
    return Book_record.objects.order_by('-published_year')[:5]


@register.simple_tag
def current_time(format_string):
    return datetime.datetime.now().strftime(format_string)