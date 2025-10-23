from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.http import HttpResponseForbidden
from django.db.models import Q
from django.contrib.auth import get_user_model
from .models import Project, Building, ProjectTeamMember, ProjectVendor
from .forms import ProjectForm, BuildingForm, ProjectTeamMemberForm, ProjectVendorForm

@login_required
def project_list(request):
    if request.user.is_staff:
        projects = Project.objects.all()
    else:
        projects = Project.objects.filter(
            Q(team_members__user=request.user) | 
            Q(vendors__user=request.user)
        ).distinct()
    
    return render(request, 'projects/project_list.html', {
        'projects': projects
    })

@login_required
def project_create(request):
    # Only Admin users can create projects
    if not (request.user.user_type == 'Admin'):
        return HttpResponseForbidden('Only Admin users may create projects.')

    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            # set the creating user as owner
            project.owner = request.user
            project.save()
            messages.success(request, 'Project created successfully.')
            return redirect('project_detail', pk=project.pk)
    else:
        form = ProjectForm()
    
    return render(request, 'projects/project_form.html', {
        'form': form,
        'title': 'Create Project'
    })

@login_required
def project_detail(request, pk):
    from .models import BuildingRole
    project = get_object_or_404(Project, pk=pk)
    buildings = project.buildings.all()
    team_members = project.team_members.select_related('user').prefetch_related(
        'user__buildingrole_set__building'
    ).all()
    vendors = project.vendors.select_related('user', 'building').prefetch_related('services').all()
    
    # Create a mapping of user to their building roles for this project
    team_member_roles = {}
    for member in team_members:
        roles = BuildingRole.objects.filter(
            user=member.user,
            building__project=project
        ).select_related('building')
        team_member_roles[member.id] = list(roles)
    
    return render(request, 'projects/project_detail.html', {
        'project': project,
        'buildings': buildings,
        'team_members': team_members,
        'team_member_roles': team_member_roles,
        'vendors': vendors
    })

@login_required
def project_edit(request, pk):
    project = get_object_or_404(Project, pk=pk)
    # Only Admin users can edit projects
    if not (request.user.user_type == 'Admin'):
        return HttpResponseForbidden('Only Admin users may edit projects.')

    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            project = form.save()
            messages.success(request, 'Project updated successfully.')
            return redirect('project_detail', pk=project.pk)
    else:
        form = ProjectForm(instance=project)
    
    return render(request, 'projects/project_form.html', {
        'form': form,
        'project': project,
        'title': 'Edit Project'
    })

@login_required
def building_create(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk)
    # Only Admin users can add buildings
    if not (request.user.user_type == 'Admin'):
        return HttpResponseForbidden('Only Admin users may add buildings.')

    if request.method == 'POST':
        form = BuildingForm(request.POST)
        if form.is_valid():
            building = form.save(commit=False)
            building.project = project
            building.save()
            messages.success(request, 'Building added successfully.')
            return redirect('project_detail', pk=project.pk)
    else:
        form = BuildingForm(initial={'project': project})
    
    return render(request, 'projects/building_form.html', {
        'form': form,
        'project': project,
        'title': 'Add Building'
    })

@login_required
def team_member_add(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk)
    # Only Admin users can add team members
    if not (request.user.user_type == 'Admin'):
        return HttpResponseForbidden('Only Admin users may add team members.')

    if request.method == 'POST':
        form = ProjectTeamMemberForm(request.POST)
        if form.is_valid():
            team_member = form.save(commit=False)
            team_member.project = project
            team_member.save()
            
            # Create BuildingRole if building and role are provided
            building = form.cleaned_data.get('building')
            role = form.cleaned_data.get('role')
            if building and role:
                from .models import BuildingRole
                BuildingRole.objects.get_or_create(
                    building=building,
                    user=team_member.user,
                    role=role
                )
                messages.success(request, f'Team member added and assigned as {role} for {building.name}.')
            else:
                messages.success(request, 'Team member added successfully.')
            
            return redirect('project_detail', pk=project.pk)
    else:
        form = ProjectTeamMemberForm(initial={'project': project})
    
    return render(request, 'projects/team_member_form.html', {
        'form': form,
        'project': project,
        'title': 'Add Team Member'
    })


@login_required
def team_member_delete(request, project_pk, member_pk):
    project = get_object_or_404(Project, pk=project_pk)
    member = get_object_or_404(ProjectTeamMember, pk=member_pk, project=project)
    # Permission: only Admins or project owner may remove the association
    is_admin = request.user.user_type == 'Admin'
    is_owner = project.owner == request.user
    if not (is_admin or is_owner or request.user == member.user):
        return HttpResponseForbidden('You do not have permission to remove this team member.')

    if request.method == 'POST':
        member.delete()
        messages.success(request, 'Team member removed successfully.')
        return redirect('project_detail', pk=project.pk)
    return render(request, 'projects/confirm_delete.html', {
        'object': member,
        'project': project,
        'type': 'team member'
    })

@login_required
def vendor_add(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk)
    # Only Admin users can add vendors to projects
    if not (request.user.user_type == 'Admin'):
        return HttpResponseForbidden('Only Admin users may add vendors to projects.')

    if request.method == 'POST':
        form = ProjectVendorForm(request.POST)
        if form.is_valid():
            vendor = form.save(commit=False)
            vendor.project = project
            vendor.save()
            # Save many-to-many services from form if provided
            if hasattr(form, 'cleaned_data') and 'services' in form.cleaned_data:
                services = form.cleaned_data.get('services')
                if services:
                    vendor.services.set(services)
            messages.success(request, 'Vendor added successfully.')
            return redirect('project_detail', pk=project.pk)
    else:
        form = ProjectVendorForm(initial={'project': project})
    
    return render(request, 'projects/vendor_form.html', {
        'form': form,
        'project': project,
        'title': 'Add Vendor'
    })


@login_required
def vendor_delete(request, project_pk, vendor_pk):
    project = get_object_or_404(Project, pk=project_pk)
    vendor = get_object_or_404(ProjectVendor, pk=vendor_pk, project=project)
    # Permission: only Admins or project owner may remove the association
    is_admin = request.user.user_type == 'Admin'
    is_owner = project.owner == request.user
    if not (is_admin or is_owner or request.user == vendor.user):
        return HttpResponseForbidden('You do not have permission to remove this vendor.')

    if request.method == 'POST':
        vendor.delete()
        messages.success(request, 'Vendor removed successfully.')
        return redirect('project_detail', pk=project.pk)
    return render(request, 'projects/confirm_delete.html', {
        'object': vendor,
        'project': project,
        'type': 'vendor'
    })

@login_required
def search_projects(request):
    term = request.GET.get('term', '')
    projects = Project.objects.filter(name__icontains=term)[:10]
    results = [{'id': p.id, 'text': p.name} for p in projects]
    return JsonResponse({'results': results})

@login_required
def search_buildings(request):
    term = request.GET.get('term', '')
    project_id = request.GET.get('project_id')
    if project_id:
        buildings = Building.objects.filter(
            project_id=project_id,
            name__icontains=term
        )[:10]
    else:
        buildings = Building.objects.filter(name__icontains=term)[:10]
    results = [{'id': b.id, 'text': b.name} for b in buildings]
    return JsonResponse({'results': results})

@login_required
def search_users(request):
    term = request.GET.get('term', '')
    users = get_user_model().objects.filter(
        Q(username__icontains=term) |
        Q(first_name__icontains=term) |
        Q(last_name__icontains=term)
    )[:10]
    results = [{'id': u.id, 'text': f"{u.get_full_name()} ({u.username})"} 
              for u in users]
    return JsonResponse({'results': results})
