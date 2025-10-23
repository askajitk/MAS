from django.contrib.auth import login, get_user_model
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.http import JsonResponse
from .forms import CustomUserCreationForm

class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('accounts:dashboard')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response

@login_required
def dashboard(request):
    context = {'user': request.user}
    
    # If user is a vendor, get their MAS list
    if request.user.user_type == 'Vendor':
        from mas_sheets.models import MAS
        context['mas_list'] = MAS.objects.filter(creator=request.user).order_by('-updated_at')[:10]
    
    return render(request, 'accounts/dashboard.html', context)

def check_username(request):
    username = request.GET.get('username', '').strip()
    User = get_user_model()
    
    if len(username) < 3:
        response = {
            'available': False,
            'message': 'Username must be at least 3 characters long'
        }
    elif len(username) > 150:
        response = {
            'available': False,
            'message': 'Username cannot be more than 150 characters long'
        }
    else:
        is_taken = User.objects.filter(username__iexact=username).exists()
        response = {
            'available': not is_taken,
            'message': 'This username is already taken' if is_taken else 'Username is available'
        }
    
    return JsonResponse(response)
