from django import template
from django.utils.translation import gettext


register = template.Library()


@register.filter(name="tr_category")
def tr_category(value):
    """Translate category names stored in DB using locale catalogs."""
    if value is None:
        return ""
    return gettext(str(value))
