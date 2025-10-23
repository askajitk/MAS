from django import template

register = template.Library()

@register.filter
def endswith(value, arg):
    """Check if a string ends with a specific substring."""
    if value and arg:
        return str(value).endswith(str(arg))
    return False

@register.filter
def is_approver_for_building(user, building):
    """Check if user is an approver for the given building."""
    from projects.models import BuildingRole
    if not user or not building:
        return False
    return BuildingRole.objects.filter(
        user=user,
        building=building,
        role='Approver'
    ).exists()

@register.filter
def is_reviewer_for_building(user, building):
    """Check if user is a reviewer for the given building."""
    from projects.models import BuildingRole
    if not user or not building:
        return False
    return BuildingRole.objects.filter(
        user=user,
        building=building,
        role='Reviewer'
    ).exists()
