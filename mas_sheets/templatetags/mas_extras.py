from django import template

register = template.Library()

@register.filter
def endswith(value, arg):
    """Check if a string ends with a specific substring."""
    if value and arg:
        return str(value).endswith(str(arg))
    return False
