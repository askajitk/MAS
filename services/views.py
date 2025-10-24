from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from .models import Service, Item, ItemMake, ServiceLog
from .forms import ServiceForm, ItemForm, ItemMakeForm

def is_staff_or_admin(user):
    return user.is_staff or user.level == 'Admin'

@login_required
@user_passes_test(is_staff_or_admin)
def service_list(request):
    services = Service.objects.all()
    return render(request, 'services/service_list.html', {
        'services': services
    })

@login_required
@user_passes_test(is_staff_or_admin)
def service_create(request):
    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            service = form.save()
            ServiceLog.objects.create(
                user=request.user,
                username=request.user.username,
                action='CREATE',
                content_type='Service',
                object_id=service.id,
                details=f'Created service: {service}'
            )
            messages.success(request, 'Service created successfully.')
            return redirect('service_list')
    else:
        form = ServiceForm()
    
    return render(request, 'services/service_form.html', {
        'form': form,
        'title': 'Create Service'
    })

@login_required
@user_passes_test(is_staff_or_admin)
def service_edit(request, pk):
    service = get_object_or_404(Service, pk=pk)
    if request.method == 'POST':
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            service = form.save()
            ServiceLog.objects.create(
                user=request.user,
                username=request.user.username,
                action='UPDATE',
                content_type='Service',
                object_id=service.id,
                details=f'Updated service: {service}'
            )
            messages.success(request, 'Service updated successfully.')
            return redirect('service_list')
    else:
        form = ServiceForm(instance=service)
    
    return render(request, 'services/service_form.html', {
        'form': form,
        'service': service,
        'title': 'Edit Service'
    })

@login_required
@user_passes_test(is_staff_or_admin)
def service_delete(request, pk):
    service = get_object_or_404(Service, pk=pk)
    if request.method == 'POST':
        ServiceLog.objects.create(
            user=request.user,
            username=request.user.username,
            action='DELETE',
            content_type='Service',
            object_id=service.id,
            details=f'Deleted service: {service}'
        )
        service.delete()
        messages.success(request, 'Service deleted successfully.')
        return redirect('service_list')
    
    return render(request, 'services/service_confirm_delete.html', {
        'service': service
    })

@login_required
@user_passes_test(is_staff_or_admin)
def service_log_view(request):
    logs = ServiceLog.objects.all().order_by('-timestamp')
    return render(request, 'services/service_log.html', {
        'logs': logs
    })

@login_required
@user_passes_test(is_staff_or_admin)
def item_list(request, service_pk):
    service = get_object_or_404(Service, pk=service_pk)
    items = service.items.all()
    return render(request, 'services/item_list.html', {
        'service': service,
        'items': items
    })

@login_required
@user_passes_test(is_staff_or_admin)
def item_create(request, service_pk):
    service = get_object_or_404(Service, pk=service_pk)
    if request.method == 'POST':
        form = ItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.service = service
            item.save()
            
            # Log item creation
            item_details = f'Created item: {item}'
            if form.cleaned_data.get('makes'):
                makes = [make.strip() for make in form.cleaned_data['makes'].split(',') if make.strip()]
                item_details += f' with makes: {", ".join(makes)}'
                # Create makes
                for make in makes:
                    ItemMake.objects.create(item=item, name=make)
                    
            ServiceLog.objects.create(
                user=request.user,
                username=request.user.username,
                action='CREATE',
                content_type='Item',
                object_id=item.id,
                details=item_details
            )
            messages.success(request, 'Item and makes created successfully.')
            return redirect('item_list', service_pk=service.pk)
    else:
        form = ItemForm(initial={'service': service})
    
    return render(request, 'services/item_form.html', {
        'form': form,
        'service': service,
        'title': 'Create Item'
    })

@login_required
@user_passes_test(is_staff_or_admin)
def item_edit(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if request.method == 'POST':
        form = ItemForm(request.POST, instance=item)
        if form.is_valid():
            # Get old makes for logging
            old_makes = set(make.name for make in item.makes.all())
            
            item = form.save()
            
            # Get new makes for logging
            new_makes = set(make.strip() for make in form.cleaned_data.get('makes', '').split(',') if make.strip())
            
            # Create log details
            changes = []
            if item.name != form.initial.get('name'):
                changes.append(f"name from '{form.initial.get('name')}' to '{item.name}'")
            
            added_makes = new_makes - old_makes
            removed_makes = old_makes - new_makes
            if added_makes:
                changes.append(f"added makes: {', '.join(added_makes)}")
            if removed_makes:
                changes.append(f"removed makes: {', '.join(removed_makes)}")
            
            details = f"Updated item {item}"
            if changes:
                details += f" - Changes: {'; '.join(changes)}"
            
            ServiceLog.objects.create(
                user=request.user,
                username=request.user.username,
                action='UPDATE',
                content_type='Item',
                object_id=item.id,
                details=details
            )
            messages.success(request, 'Item and makes updated successfully.')
            return redirect('item_list', service_pk=item.service.pk)
    else:
        form = ItemForm(instance=item)
    
    return render(request, 'services/item_form.html', {
        'form': form,
        'item': item,
        'service': item.service,
        'title': 'Edit Item'
    })

@login_required
@user_passes_test(is_staff_or_admin)
def item_delete(request, pk):
    item = get_object_or_404(Item, pk=pk)
    service_pk = item.service.pk
    if request.method == 'POST':
        ServiceLog.objects.create(
            user=request.user,
            username=request.user.username,
            action='DELETE',
            content_type='Item',
            object_id=item.id,
            details=f'Deleted item: {item}'
        )
        item.delete()
        messages.success(request, 'Item deleted successfully.')
        return redirect('item_list', service_pk=service_pk)
    
    return render(request, 'services/item_confirm_delete.html', {
        'item': item
    })
