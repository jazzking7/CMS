from django import template

register = template.Library()

@register.filter
def contains(value, substring):
    """
    Checks if a substring is present in a string.
    """
    if not isinstance(value, str) or not isinstance(substring, str):
        return False
    return substring in value
