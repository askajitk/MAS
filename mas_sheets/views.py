from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.db.models import Q
from .models import MAS
from .forms import MASForm
from .decorators import reviewer_required, approver_required
from projects.models import Building
from services.models import Service, Item
from projects.models import ProjectVendor

@login_required
def mas_create(request):
    if request.method == 'POST':
        form = MASForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            mas = form.save(commit=False)
            mas.creator = request.user
            mas.save()
            messages.success(request, 'MAS created successfully.')
            return redirect('mas_sheets:mas_list')
    else:
        form = MASForm(user=request.user)
    
    return render(request, 'mas_sheets/mas_form.html', {'form': form})

@login_required
def mas_edit(request, pk):
    mas = get_object_or_404(MAS, pk=pk)
    
    # Check if user is the creator and MAS is still pending
    if not (request.user == mas.creator and mas.can_edit()):
        raise PermissionDenied
    
    if request.method == 'POST':
        form = MASForm(request.POST, request.FILES, instance=mas, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'MAS updated successfully.')
            return redirect('mas_sheets:mas_list')
    else:
        form = MASForm(instance=mas, user=request.user)
    
    return render(request, 'mas_sheets/mas_form.html', {'form': form, 'mas': mas})

@login_required
def mas_list(request):
    status_filter = request.GET.get('status', 'pending')
    
    if request.user.user_type == 'Admin':
        mas_list = MAS.objects.all()
    elif request.user.user_type == 'Team':
        # Team members see MAS based on their building role assignments
        from projects.models import BuildingRole
        
        # Get all buildings where this user has any role
        reviewer_buildings = BuildingRole.objects.filter(
            user=request.user, role='Reviewer'
        ).values_list('building', flat=True)
        
        approver_buildings = BuildingRole.objects.filter(
            user=request.user, role='Approver'
        ).values_list('building', flat=True)
        
        # Show MAS for buildings where user is reviewer (pending_review) or approver (pending_approval)
        mas_filter = Q()
        if reviewer_buildings:
            mas_filter |= Q(building_id__in=reviewer_buildings, status='pending_review')
        if approver_buildings:
            mas_filter |= Q(building_id__in=approver_buildings, status='pending_approval')
        
        # Also show approved/rejected MAS from their buildings
        all_buildings = list(reviewer_buildings) + list(approver_buildings)
        if all_buildings:
            mas_filter |= Q(building_id__in=all_buildings, status__in=['approved', 'rejected'])
        
        if mas_filter:
            mas_list = MAS.objects.filter(mas_filter)
        else:
            mas_list = MAS.objects.none()
    else:  # Vendor
        mas_list = MAS.objects.filter(creator=request.user)
    
    # Apply status filter
    if status_filter == 'pending':
        mas_list = mas_list.filter(
            Q(status='pending_review') |
            Q(status='pending_approval') |
            Q(status='revision_requested')
        )
    elif status_filter in ['approved', 'rejected']:
        mas_list = mas_list.filter(status=status_filter)
    
    context = {
        'mas_list': mas_list,
        'status_filter': status_filter,
    }
    return render(request, 'mas_sheets/mas_list.html', context)

# AJAX views for dynamic form updates
@login_required
def load_buildings(request):
    project_id = request.GET.get('project')
    # If the user has a vendor assignment with a specific building, return that only
    try:
        pv = ProjectVendor.objects.get(project_id=project_id, user=request.user)
        if pv.building:
            buildings = Building.objects.filter(pk=pv.building.pk)
        else:
            buildings = Building.objects.filter(project_id=project_id).order_by('name')
    except ProjectVendor.DoesNotExist:
        buildings = Building.objects.filter(project_id=project_id).order_by('name')
    return JsonResponse(list(buildings.values('id', 'name')), safe=False)

@login_required
def load_services(request):
    project_id = request.GET.get('project')
    # If vendor has assigned services for this project, return only those
    try:
        pv = ProjectVendor.objects.get(project_id=project_id, user=request.user)
        assigned = pv.services.all()
        if assigned.exists():
            services = assigned.order_by('name')
        else:
            services = Service.objects.all().order_by('name')
    except ProjectVendor.DoesNotExist:
        services = Service.objects.all().order_by('name')
    return JsonResponse(list(services.values('id', 'name')), safe=False)

@login_required
def load_items(request):
    service_id = request.GET.get('service')
    items = Item.objects.filter(service_id=service_id).order_by('name')
    return JsonResponse(list(items.values('id', 'name')), safe=False)

@login_required
def load_makes(request):
    item_id = request.GET.get('item')
    from services.models import ItemMake
    makes = ItemMake.objects.filter(item_id=item_id).values('id', 'name').order_by('name')
    makes_list = list(makes)
    # Add "Other" option at the end
    makes_list.append({'id': 'other', 'name': 'Other'})
    return JsonResponse(makes_list, safe=False)

@login_required
def review_mas(request, pk):
    mas = get_object_or_404(MAS, pk=pk)
    
    # Verify user is assigned as Reviewer for this building
    from projects.models import BuildingRole
    if not BuildingRole.objects.filter(
        building=mas.building, user=request.user, role='Reviewer'
    ).exists():
        raise PermissionDenied
    
    if request.method == 'POST':
        action = request.POST.get('action')
        comment = request.POST.get('comment', '').strip()
        
        if action not in ['approve', 'reject', 'comment']:
            messages.error(request, 'Invalid action.')
            return redirect('mas_sheets:review_mas', pk=pk)
        
        if (action == 'reject' or action == 'comment') and not comment:
            messages.error(request, 'Comment is required for rejection or revision request.')
            return redirect('mas_sheets:review_mas', pk=pk)
        
        mas.review_comment = comment
        mas.review_date = timezone.now()
        mas.reviewer = request.user
        
        if action == 'approve':
            mas.status = 'pending_approval'
            msg = 'MAS has been approved and sent to final approver.'
        elif action == 'reject':
            mas.status = 'rejected'
            msg = 'MAS has been rejected.'
        else:  # comment
            mas.status = 'revision_requested'
            msg = 'Revision requested from vendor.'
        
        mas.save()
        messages.success(request, msg)
        return redirect('mas_sheets:mas_list')
    
    return render(request, 'mas_sheets/review_mas.html', {'mas': mas})

@login_required
def approve_mas(request, pk):
    mas = get_object_or_404(MAS, pk=pk, status='pending_approval')
    
    # Verify user is assigned as Approver for this building
    from projects.models import BuildingRole
    if not BuildingRole.objects.filter(
        building=mas.building, user=request.user, role='Approver'
    ).exists():
        raise PermissionDenied
    
    if request.method == 'POST':
        action = request.POST.get('action')
        comment = request.POST.get('comment', '').strip()
        
        if action not in ['approve', 'reject']:
            messages.error(request, 'Invalid action.')
            return redirect('mas_sheets:approve_mas', pk=pk)
        
        if action == 'reject' and not comment:
            messages.error(request, 'Comment is required for rejection.')
            return redirect('mas_sheets:approve_mas', pk=pk)
        
        mas.approval_comment = comment
        mas.approval_date = timezone.now()
        mas.approver = request.user
        mas.status = 'approved' if action == 'approve' else 'rejected'
        mas.save()
        
        msg = 'MAS has been approved.' if action == 'approve' else 'MAS has been rejected.'
        messages.success(request, msg)
        return redirect('mas_sheets:mas_list')
    
    return render(request, 'mas_sheets/approve_mas.html', {'mas': mas})

@login_required
def mas_revision(request, pk):
    mas = get_object_or_404(MAS, pk=pk)
    
    # Check if user is the creator and MAS needs revision
    if not (request.user == mas.creator and mas.status in ['rejected', 'revision_requested']):
        raise PermissionDenied
    
    if request.method == 'POST':
        form = MASForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            new_mas = form.save(commit=False)
            
            # Copy the MAS ID and increment revision
            new_mas.mas_id = mas.mas_id
            rev_num = int(mas.revision[1:])
            new_mas.revision = f'R{rev_num + 1}'
            
            new_mas.creator = request.user
            new_mas.status = 'pending_review'
            new_mas.save()
            
            messages.success(request, f'Revision {new_mas.revision} submitted successfully.')
            return redirect('mas_sheets:mas_list')
    else:
        # Pre-fill form with existing data
        form = MASForm(instance=mas, user=request.user)
    
    context = {
        'form': form,
        'mas': mas,
        'is_revision': True
    }
    return render(request, 'mas_sheets/mas_form.html', context)
