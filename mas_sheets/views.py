from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.db.models import Q
from .models import MAS, MASActivityLog
from .forms import MASForm
from .decorators import reviewer_required, approver_required
from projects.models import Building, Project
from services.models import Service, Item
from projects.models import ProjectVendor
from accounts.models import CustomUser

@login_required
def mas_create(request):
    if request.method == 'POST':
        form = MASForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            mas = form.save(commit=False)
            mas.creator = request.user
            # Set the make value from cleaned_data
            mas.make = form.cleaned_data.get('make')
            mas.save()
            # Log activity
            mas.log_activity('created', request.user, 'MAS created')
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
            mas = form.save(commit=False)
            # Set the make value from cleaned_data
            mas.make = form.cleaned_data.get('make')
            mas.save()
            # Log activity
            mas.log_activity('edited', request.user, 'MAS updated')
            messages.success(request, 'MAS updated successfully.')
            return redirect('mas_sheets:mas_list')
    else:
        form = MASForm(instance=mas, user=request.user)
    
    return render(request, 'mas_sheets/mas_form.html', {'form': form, 'mas': mas})

@login_required
def mas_list(request):
    status_filter = request.GET.get('status', 'pending')
    
    if request.user.user_type == 'Admin':
        mas_list = MAS.objects.filter(is_latest=True)
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
        
        all_buildings = list(set(list(reviewer_buildings) + list(approver_buildings)))
        
        # Filter based on status_filter - only show latest revisions
        if status_filter == 'pending':
            # Show MAS pending with reviewer (pending_review status)
            mas_list = MAS.objects.filter(
                building_id__in=reviewer_buildings,
                status='pending_review',
                is_latest=True
            )
        elif status_filter == 'pending_approval':
            # Show MAS pending with approver
            # Reviewers can see MAS from their buildings that are pending approval
            # Approvers can see MAS from their buildings that need approval
            mas_list = MAS.objects.filter(
                building_id__in=all_buildings,
                status='pending_approval',
                is_latest=True
            )
        elif status_filter == 'approved':
            # Show MAS approved by approver
            mas_list = MAS.objects.filter(
                building_id__in=all_buildings,
                status='approved',
                is_latest=True
            )
        elif status_filter == 'rejected':
            # Show MAS rejected by reviewer or approver
            mas_list = MAS.objects.filter(
                building_id__in=all_buildings,
                status='rejected',
                is_latest=True
            )
        else:
            mas_list = MAS.objects.none()
            
        # Get count of pending approval for badge display
        # Show count of MAS that are pending approval in all assigned buildings
        pending_approval_count = MAS.objects.filter(
            building_id__in=all_buildings,
            status='pending_approval',
            is_latest=True
        ).count()
    else:  # Vendor
        mas_list = MAS.objects.filter(creator=request.user, is_latest=True)
        pending_approval_count = 0
        
        # Apply status filter for vendors
        if status_filter == 'pending':
            mas_list = mas_list.filter(
                Q(status='pending_review') |
                Q(status='pending_approval') |
                Q(status='revision_requested')
            )
        elif status_filter == 'pending_approval':
            mas_list = mas_list.filter(status='pending_approval')
        elif status_filter in ['approved', 'rejected']:
            mas_list = mas_list.filter(status=status_filter)
    
    context = {
        'mas_list': mas_list,
        'status_filter': status_filter,
        'pending_approval_count': pending_approval_count if request.user.user_type == 'Team' else 0,
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
    project_id = request.GET.get('project')
    items = Item.objects.filter(service_id=service_id).order_by('name')
    # If project provided, exclude items already covered by a latest MAS for this vendor in that project
    if project_id:
        blocked_item_ids = MAS.objects.filter(
            creator=request.user,
            project_id=project_id,
            is_latest=True,
        ).values_list('item_id', flat=True)
        items = items.exclude(id__in=list(blocked_item_ids))
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
            log_action = 'submitted_approval'
            log_details = f'Reviewed and sent for approval. Comment: {comment}' if comment else 'Reviewed and sent for approval'
        elif action == 'reject':
            mas.status = 'rejected'
            msg = 'MAS has been rejected.'
            log_action = 'rejected'
            log_details = f'Rejected by reviewer. Comment: {comment}'
        else:  # comment
            mas.status = 'revision_requested'
            msg = 'Revision requested from vendor.'
            log_action = 'revision_requested'
            log_details = f'Revision requested. Comment: {comment}'
        
        mas.save()
        # Log activity
        mas.log_activity(log_action, request.user, log_details)
        messages.success(request, msg)
        return redirect('mas_sheets:mas_list')
    
    # Get revision history
    revision_history = mas.get_revision_history()
    
    return render(request, 'mas_sheets/review_mas.html', {
        'mas': mas,
        'revision_history': revision_history
    })

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
        
        # Log activity
        if action == 'approve':
            log_details = f'Approved by approver. Comment: {comment}' if comment else 'Approved by approver'
            mas.log_activity('approved', request.user, log_details)
        else:
            log_details = f'Rejected by approver. Comment: {comment}'
            mas.log_activity('rejected', request.user, log_details)
        
        msg = 'MAS has been approved.' if action == 'approve' else 'MAS has been rejected.'
        messages.success(request, msg)
        return redirect('mas_sheets:mas_list')
    
    # Get revision history
    revision_history = mas.get_revision_history()
    
    return render(request, 'mas_sheets/approve_mas.html', {
        'mas': mas,
        'revision_history': revision_history
    })

@login_required
def mas_revision(request, pk):
    mas = get_object_or_404(MAS, pk=pk)
    
    # Check if user is the creator and MAS needs revision
    if not (request.user == mas.creator and mas.status in ['rejected', 'revision_requested']):
        raise PermissionDenied
    
    # Only allow submitting a revision from the latest revision of this MAS chain
    if not mas.is_latest:
        latest = MAS.objects.filter(mas_id=mas.mas_id, is_latest=True).first()
        if latest:
            if latest.status in ['rejected', 'revision_requested']:
                messages.warning(request, 'Please submit revisions from the latest revision only. Redirected to the latest.')
                return redirect('mas_sheets:mas_revision', pk=latest.pk)
            else:
                messages.info(request, 'The latest revision is not requesting changes. No new revision can be submitted.')
                return redirect('mas_sheets:mas_list')
        # Fallback: if no latest found (should not happen), send to list
        messages.warning(request, 'Please submit revisions from the latest revision only.')
        return redirect('mas_sheets:mas_list')
    
    if request.method == 'POST':
        form = MASForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            # Create a new MAS record for the revision
            new_mas = form.save(commit=False)
            
            # Copy key fields from the original
            new_mas.mas_id = mas.mas_id
            new_mas.serial_number = mas.serial_number
            
            # Set revision number
            rev_num = int(mas.revision[1:])
            new_mas.revision = f'R{rev_num + 1}'
            
            # Link to parent
            new_mas.parent_mas = mas if mas.parent_mas is None else mas.parent_mas
            new_mas.is_latest = True
            
            # Set creator and status
            new_mas.creator = request.user
            new_mas.status = 'pending_review'
            
            # Set the make value from cleaned_data
            new_mas.make = form.cleaned_data.get('make')
            
            # Save the new revision (the model's save() method will mark old revisions as not latest)
            new_mas.save()
            
            # Log activity
            new_mas.log_activity('revision_submitted', request.user, f'Revision {new_mas.revision} submitted')
            
            messages.success(request, f'Revision {new_mas.revision} submitted successfully.')
            return redirect('mas_sheets:mas_list')
    else:
        # Pre-fill form with existing data
        form = MASForm(instance=mas, user=request.user)
    
    context = {
        'form': form,
        'mas': mas,
        'is_revision': True,
        'revision_history': mas.get_revision_history()
    }
    return render(request, 'mas_sheets/mas_form.html', context)


@login_required
def mas_history(request):
    """View for MAS activity history with filters"""
    
    # Get all activity logs
    logs = MASActivityLog.objects.all().select_related('mas', 'user')
    
    # Filter based on user type
    if request.user.user_type == 'Admin':
        # Admin sees all logs
        pass
    elif request.user.user_type == 'Team':
        # Team members see logs from their assigned buildings
        from projects.models import BuildingRole
        assigned_buildings = BuildingRole.objects.filter(user=request.user).values_list('building', flat=True)
        logs = logs.filter(mas__building_id__in=assigned_buildings)
    else:  # Vendor
        # Vendors see only their own MAS logs
        logs = logs.filter(mas__creator=request.user)
    
    # Apply filters
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    created_by = request.GET.get('created_by')
    reviewed_by = request.GET.get('reviewed_by')
    approved_by = request.GET.get('approved_by')
    service = request.GET.get('service')
    item = request.GET.get('item')
    make = request.GET.get('make')
    project = request.GET.get('project')
    building = request.GET.get('building')
    action = request.GET.get('action')
    mas_id = request.GET.get('mas_id')
    
    if date_from:
        logs = logs.filter(timestamp__date__gte=date_from)
    if date_to:
        logs = logs.filter(timestamp__date__lte=date_to)
    if created_by:
        logs = logs.filter(mas__creator_id=created_by)
    if reviewed_by:
        logs = logs.filter(mas__reviewer_id=reviewed_by)
    if approved_by:
        logs = logs.filter(mas__approver_id=approved_by)
    if service:
        logs = logs.filter(mas__service_id=service)
    if item:
        logs = logs.filter(mas__item_id=item)
    if make:
        logs = logs.filter(make=make)
    if project:
        logs = logs.filter(mas__project_id=project)
    if building:
        logs = logs.filter(mas__building_id=building)
    if action:
        logs = logs.filter(action=action)
    if mas_id:
        logs = logs.filter(mas__mas_id__icontains=mas_id)
    
    # Get filter options for dropdowns based on user type
    if request.user.user_type == 'Admin':
        # Admin sees all options
        users = CustomUser.objects.filter(is_active=True).order_by('username')
        projects_list = Project.objects.all().order_by('name')
        buildings_list = Building.objects.all().order_by('name')
        services_list = Service.objects.all().order_by('name')
        items_list = Item.objects.all().order_by('name')
    elif request.user.user_type == 'Team':
        # Team members see options from their assigned buildings
        from projects.models import BuildingRole
        assigned_buildings = BuildingRole.objects.filter(user=request.user).values_list('building', flat=True)
        assigned_projects = Building.objects.filter(id__in=assigned_buildings).values_list('project', flat=True).distinct()
        
        users = CustomUser.objects.filter(
            Q(id=request.user.id) |  # Self
            Q(created_mas__building_id__in=assigned_buildings) |  # Vendors who created MAS in their buildings
            Q(reviewed_mas__building_id__in=assigned_buildings) |  # Reviewers
            Q(approved_mas__building_id__in=assigned_buildings)  # Approvers
        ).filter(is_active=True).distinct().order_by('username')
        
        projects_list = Project.objects.filter(id__in=assigned_projects).order_by('name')
        buildings_list = Building.objects.filter(id__in=assigned_buildings).order_by('name')
        
        # Get services and items from MAS in their buildings
        services_in_buildings = MAS.objects.filter(building_id__in=assigned_buildings).values_list('service', flat=True).distinct()
        items_in_buildings = MAS.objects.filter(building_id__in=assigned_buildings).values_list('item', flat=True).distinct()
        
        services_list = Service.objects.filter(id__in=services_in_buildings).order_by('name')
        items_list = Item.objects.filter(id__in=items_in_buildings).order_by('name')
    else:  # Vendor
        # Vendors see options from their own projects/buildings
        vendor_projects = ProjectVendor.objects.filter(user=request.user).values_list('project', flat=True)
        vendor_buildings = ProjectVendor.objects.filter(user=request.user).values_list('building', flat=True)
        
        # Users: self and team members from their projects
        users = CustomUser.objects.filter(
            Q(id=request.user.id) |  # Self
            Q(buildingrole__building__project_id__in=vendor_projects)  # Team members in their projects
        ).filter(is_active=True).distinct().order_by('username')
        
        projects_list = Project.objects.filter(id__in=vendor_projects).order_by('name')
        
        # Buildings from vendor assignments or where they created MAS
        buildings_from_assignment = Building.objects.filter(id__in=vendor_buildings)
        buildings_from_mas = Building.objects.filter(mas__creator=request.user)
        buildings_list = (buildings_from_assignment | buildings_from_mas).distinct().order_by('name')
        
        # Services and items from vendor assignments or their MAS
        vendor_services = ProjectVendor.objects.filter(user=request.user).values_list('services', flat=True)
        services_from_mas = MAS.objects.filter(creator=request.user).values_list('service', flat=True).distinct()
        services_list = Service.objects.filter(
            Q(id__in=vendor_services) | Q(id__in=services_from_mas)
        ).distinct().order_by('name')
        
        items_from_mas = MAS.objects.filter(creator=request.user).values_list('item', flat=True).distinct()
        items_list = Item.objects.filter(id__in=items_from_mas).order_by('name')
    
    actions_list = MASActivityLog.ACTION_CHOICES

    # Build MAS ID options for the MAS ID filter (typed input + suggestions)
    # Scope suggestions to the user's visibility
    if request.user.user_type == 'Admin':
        mas_id_options_qs = MAS.objects.all()
    elif request.user.user_type == 'Team':
        from projects.models import BuildingRole
        assigned_buildings = BuildingRole.objects.filter(user=request.user).values_list('building', flat=True)
        mas_id_options_qs = MAS.objects.filter(building_id__in=assigned_buildings)
    else:  # Vendor
        mas_id_options_qs = MAS.objects.filter(creator=request.user)
    mas_id_options = mas_id_options_qs.values_list('mas_id', flat=True).distinct().order_by('mas_id')[:1000]
    
    # Get unique makes from the filtered logs for the make dropdown
    # Get makes before applying the make filter
    temp_logs = logs
    if make:
        # Remove the make filter temporarily to get all makes
        if request.user.user_type == 'Admin':
            temp_logs = MASActivityLog.objects.all()
        elif request.user.user_type == 'Team':
            from projects.models import BuildingRole
            assigned_buildings = BuildingRole.objects.filter(user=request.user).values_list('building', flat=True)
            temp_logs = MASActivityLog.objects.filter(mas__building_id__in=assigned_buildings)
        else:  # Vendor
            temp_logs = MASActivityLog.objects.filter(mas__creator=request.user)
    
    makes_list = temp_logs.exclude(make='').values_list('make', flat=True).distinct().order_by('make')
    
    # Count active filters for UI badge
    filters_dict = {
        'date_from': date_from or '',
        'date_to': date_to or '',
        'created_by': created_by or '',
        'reviewed_by': reviewed_by or '',
        'approved_by': approved_by or '',
        'service': service or '',
        'item': item or '',
        'make': make or '',
        'project': project or '',
        'building': building or '',
        'action': action or '',
        'mas_id': mas_id or '',
    }
    filters_active_count = sum(1 for v in filters_dict.values() if v)

    context = {
        'logs': logs[:500],  # Limit to 500 records for performance
        'users': users,
        'projects': projects_list,
        'buildings': buildings_list,
        'services': services_list,
        'items': items_list,
        'makes': makes_list,
        'actions': actions_list,
    'mas_ids': mas_id_options,
        'filters': filters_dict,
        'filters_active_count': filters_active_count,
    }
    return render(request, 'mas_sheets/mas_history.html', context)
