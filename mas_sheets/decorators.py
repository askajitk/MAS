from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import user_passes_test
from functools import wraps

def reviewer_required(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if request.user.level == 'Reviewer':
            return function(request, *args, **kwargs)
        raise PermissionDenied
    return wrap

def approver_required(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if request.user.level == 'Approver':
            return function(request, *args, **kwargs)
        raise PermissionDenied
    return wrap