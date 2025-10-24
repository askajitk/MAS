from django.contrib.auth import login, get_user_model
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages
from .forms import CustomUserCreationForm
from .models import CustomUser

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
    
    # If user is a Team member (Reviewer/Approver), redirect to MAS list
    if request.user.user_type == 'Team':
        return redirect('mas_sheets:mas_list')
    
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

@login_required
def user_list(request):
    """View for admins to see all users"""
    if request.user.user_type != 'Admin':
        return HttpResponseForbidden('Only Admin users can manage users.')
    
    from projects.models import Project, ProjectVendor, BuildingRole
    
    users = CustomUser.objects.all().order_by('-date_joined')
    
    # Filter by project if specified
    project_filter = request.GET.get('project')
    if project_filter:
        # Get users assigned to this project (vendors and team members)
        vendor_users = ProjectVendor.objects.filter(project_id=project_filter).values_list('user_id', flat=True)
        team_users = BuildingRole.objects.filter(building__project_id=project_filter).values_list('user_id', flat=True)
        user_ids = list(set(list(vendor_users) + list(team_users)))
        users = users.filter(id__in=user_ids)
    
    # Filter by user type if specified
    user_type_filter = request.GET.get('user_type')
    if user_type_filter:
        users = users.filter(user_type=user_type_filter)
    
    # Get all projects for the filter dropdown
    projects = Project.objects.all().order_by('name')
    
    # Get project assignments for each user
    user_projects = {}
    for user in users:
        # Get projects where user is vendor
        vendor_projects = list(Project.objects.filter(vendors__user=user).distinct())
        # Get projects where user is team member (has building role)
        team_projects = list(Project.objects.filter(buildings__role_assignments__user=user).distinct())
        # Combine and deduplicate by project ID
        seen_ids = set()
        unique_projects = []
        for project in vendor_projects + team_projects:
            if project.id not in seen_ids:
                seen_ids.add(project.id)
                unique_projects.append(project)
        user_projects[user.id] = unique_projects
    
    context = {
        'users': users,
        'projects': projects,
        'project_filter': project_filter,
        'user_type_filter': user_type_filter,
        'user_projects': user_projects,
    }
    
    return render(request, 'accounts/user_list.html', context)

@login_required
def user_create(request):
    """View for admins to create new users"""
    if request.user.user_type != 'Admin':
        return HttpResponseForbidden('Only Admin users can create users.')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User {user.username} created successfully.')
            return redirect('accounts:user_list')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'accounts/user_form.html', {
        'form': form,
        'title': 'Create User',
        'action': 'Create'
    })

@login_required
def user_edit(request, pk):
    """View for admins to edit existing users"""
    if request.user.user_type != 'Admin':
        return HttpResponseForbidden('Only Admin users can edit users.')
    
    user = get_object_or_404(CustomUser, pk=pk)
    
    if request.method == 'POST':
        # Create a form that doesn't require password
        form = CustomUserCreationForm(request.POST, instance=user)
        # Make password fields not required for editing
        form.fields['password1'].required = False
        form.fields['password2'].required = False
        
        if form.is_valid():
            user = form.save(commit=False)
            # Only update password if provided
            if form.cleaned_data.get('password1'):
                user.set_password(form.cleaned_data['password1'])
            user.save()
            messages.success(request, f'User {user.username} updated successfully.')
            return redirect('accounts:user_list')
    else:
        form = CustomUserCreationForm(instance=user)
        # Make password fields not required for editing
        form.fields['password1'].required = False
        form.fields['password2'].required = False
        form.fields['password1'].help_text = 'Leave blank to keep the current password.'
    
    return render(request, 'accounts/user_form.html', {
        'form': form,
        'title': 'Edit User',
        'action': 'Update',
        'user_obj': user
    })

@login_required
def user_delete(request, pk):
    """View for admins to delete users"""
    if request.user.user_type != 'Admin':
        return HttpResponseForbidden('Only Admin users can delete users.')
    
    user = get_object_or_404(CustomUser, pk=pk)
    
    # Prevent admin from deleting themselves
    if user == request.user:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('accounts:user_list')
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'User {username} deleted successfully.')
        return redirect('accounts:user_list')
    
    return render(request, 'accounts/user_confirm_delete.html', {'user_obj': user})

@login_required
def project_users(request, project_pk):
    """View for admins to see all users assigned to a specific project"""
    if request.user.user_type != 'Admin':
        return HttpResponseForbidden('Only Admin users can view project users.')
    
    from projects.models import Project, ProjectVendor, BuildingRole, Building
    
    project = get_object_or_404(Project, pk=project_pk)
    
    # Get vendors assigned to this project
    vendors = CustomUser.objects.filter(projectvendor__project=project).distinct()
    
    # Get team members assigned to buildings in this project
    team_members = CustomUser.objects.filter(
        buildingrole__building__project=project
    ).distinct()
    
    # Get building roles for team members
    building_roles = {}
    for member in team_members:
        roles = BuildingRole.objects.filter(
            user=member,
            building__project=project
        ).select_related('building')
        building_roles[member.id] = roles
    
    # Get vendor assignments
    vendor_assignments = {}
    for vendor in vendors:
        assignment = ProjectVendor.objects.filter(
            user=vendor,
            project=project
        ).select_related('building').prefetch_related('services').first()
        vendor_assignments[vendor.id] = assignment
    
    context = {
        'project': project,
        'vendors': vendors,
        'team_members': team_members,
        'building_roles': building_roles,
        'vendor_assignments': vendor_assignments,
    }
    
    return render(request, 'accounts/project_users.html', context)

@login_required
def unassign_team_member(request, project_pk, user_pk):
    """Admin-only: remove a Team user from a project without deleting the user.
    This deletes any BuildingRole assignments for the project's buildings and the ProjectTeamMember link.
    """
    if request.user.user_type != 'Admin':
        return HttpResponseForbidden('Only Admin users can modify project assignments.')

    from projects.models import Project, BuildingRole, ProjectTeamMember

    project = get_object_or_404(Project, pk=project_pk)
    user = get_object_or_404(CustomUser, pk=user_pk)

    if request.method == 'POST':
        # Remove any building role assignments for this project's buildings
        BuildingRole.objects.filter(user=user, building__project=project).delete()
        # Remove project-level team member association if present
        ProjectTeamMember.objects.filter(project=project, user=user).delete()
        messages.success(request, f'Removed {user.username} from project {project.name}.')
        next_url = request.POST.get('next')
        if next_url and isinstance(next_url, str) and next_url.startswith('/'):
            return redirect(next_url)
    else:
        messages.error(request, 'Invalid request method.')

    return redirect('accounts:project_users', project_pk=project_pk)

@login_required
def unassign_vendor(request, project_pk, user_pk):
    """Admin-only: remove a Vendor user from a project without deleting the user.
    This deletes the ProjectVendor row for that project and user.
    """
    if request.user.user_type != 'Admin':
        return HttpResponseForbidden('Only Admin users can modify project assignments.')

    from projects.models import Project, ProjectVendor

    project = get_object_or_404(Project, pk=project_pk)
    user = get_object_or_404(CustomUser, pk=user_pk)

    if request.method == 'POST':
        ProjectVendor.objects.filter(project=project, user=user).delete()
        messages.success(request, f'Removed vendor {user.username} from project {project.name}.')
        next_url = request.POST.get('next')
        if next_url and isinstance(next_url, str) and next_url.startswith('/'):
            return redirect(next_url)
    else:
        messages.error(request, 'Invalid request method.')

    return redirect('accounts:project_users', project_pk=project_pk)
