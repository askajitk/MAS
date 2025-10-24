from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.db.models import Count, Avg, F, ExpressionWrapper, DurationField, Q
from django.utils import timezone
from datetime import timedelta
from mas_sheets.models import MAS, MASActivityLog
from projects.models import Project
from services.models import Item, Service
from accounts.models import CustomUser


@login_required
def analytics_dashboard(request):
    """
    Analytics dashboard for Admin users showing comprehensive MAS statistics and trends
    """
    if request.user.user_type != 'Admin':
        return HttpResponseForbidden('Only Admin users can access the analytics dashboard.')
    
    # Get all MAS records
    all_mas = MAS.objects.all()
    
    # Calculate time periods
    now = timezone.now()
    last_quarter_start = now - timedelta(days=90)
    last_30_days_start = now - timedelta(days=30)
    
    # NEW METRICS
    # 1. MAS processed so far (all approved MAS)
    mas_processed_total = all_mas.filter(status='approved').count()
    
    # 2. MAS processed in last quarter
    mas_processed_last_quarter = all_mas.filter(
        status='approved',
        approval_date__gte=last_quarter_start
    ).count()
    
    # 3. MAS processed in last 30 days
    mas_processed_last_30_days = all_mas.filter(
        status='approved',
        approval_date__gte=last_30_days_start
    ).count()
    
    # 4. Open / under review MAS in system
    open_mas_count = all_mas.filter(
        status__in=['pending_review', 'pending_approval', 'revision_requested']
    ).count()
    
    # 5. Reviewer summary: how many MAS with which reviewer
    reviewer_summary = list(all_mas.filter(
        reviewer__isnull=False
    ).values('reviewer__username').annotate(
        count=Count('id')
    ).order_by('-count'))
    
    # 6. Service wise open MAS count
    service_wise_open = list(all_mas.filter(
        status__in=['pending_review', 'pending_approval', 'revision_requested']
    ).values('service__name').annotate(
        count=Count('id')
    ).order_by('-count'))
    
    # 7. Service wise average Turn Around Time for last 90 days
    service_wise_tat = []
    services_with_approved = all_mas.filter(
        status='approved',
        approval_date__gte=last_quarter_start,
        approval_date__isnull=False
    ).values('service__name').distinct()
    
    for service in services_with_approved:
        service_name = service['service__name']
        if service_name:
            approved_in_service = all_mas.filter(
                service__name=service_name,
                status='approved',
                approval_date__gte=last_quarter_start,
                approval_date__isnull=False
            )
            
            if approved_in_service.exists():
                total_seconds = sum([
                    (m.approval_date - m.created_at).total_seconds()
                    for m in approved_in_service
                ])
                avg_seconds = total_seconds / approved_in_service.count()
                service_wise_tat.append({
                    'service': service_name,
                    'avg_days': round(avg_seconds / 86400, 1),
                    'avg_hours': round(avg_seconds / 3600, 1),
                    'count': approved_in_service.count()
                })
    
    service_wise_tat = sorted(service_wise_tat, key=lambda x: x['avg_days'])
    
    # 1. Project-wise statistics
    project_stats = list(all_mas.values('project__name').annotate(
        total=Count('id'),
        approved=Count('id', filter=Q(status='approved')),
        pending=Count('id', filter=Q(status__in=['pending_review', 'pending_approval'])),
        rejected=Count('id', filter=Q(status='rejected'))
    ).order_by('-total')[:10])
    
    # 2. Item-wise statistics
    item_stats = list(all_mas.values('item__name', 'service__name').annotate(
        total=Count('id'),
        approved=Count('id', filter=Q(status='approved'))
    ).order_by('-total')[:10])
    
    # 3. Vendor-wise statistics
    vendor_stats = list(all_mas.values('creator__username').annotate(
        total=Count('id'),
        approved=Count('id', filter=Q(status='approved')),
        pending=Count('id', filter=Q(status__in=['pending_review', 'pending_approval'])),
        rejected=Count('id', filter=Q(status='rejected')),
        revision_requested=Count('id', filter=Q(status='revision_requested'))
    ).order_by('-total')[:10])
    
    # 4. Overall statistics
    total_mas = all_mas.count()
    approved_mas = all_mas.filter(status='approved').count()
    pending_mas = all_mas.filter(status__in=['pending_review', 'pending_approval']).count()
    rejected_mas = all_mas.filter(status='rejected').count()
    revision_requested_mas = all_mas.filter(status='revision_requested').count()
    
    # 5. Revision and rejection counts
    # Count how many MAS have revisions (parent_mas is not None means it's a revision)
    mas_with_revisions = all_mas.exclude(parent_mas__isnull=True).values('mas_id').distinct().count()
    total_revisions = all_mas.exclude(parent_mas__isnull=True).count()
    
    # 6. Average approval time (from creation to approval)
    approved_mas_with_dates = MAS.objects.filter(
        status='approved',
        approval_date__isnull=False
    ).annotate(
        time_to_approve=ExpressionWrapper(
            F('approval_date') - F('created_at'),
            output_field=DurationField()
        )
    )
    
    avg_approval_time = None
    if approved_mas_with_dates.exists():
        avg_seconds = sum([m.time_to_approve.total_seconds() for m in approved_mas_with_dates]) / approved_mas_with_dates.count()
        avg_approval_time = {
            'days': int(avg_seconds // 86400),
            'hours': int((avg_seconds % 86400) // 3600),
            'minutes': int((avg_seconds % 3600) // 60)
        }
    
    # 7. Monthly trends (last 6 months)
    six_months_ago = timezone.now() - timedelta(days=180)
    monthly_data = []
    for i in range(6):
        month_start = six_months_ago + timedelta(days=30*i)
        month_end = month_start + timedelta(days=30)
        month_mas = all_mas.filter(created_at__gte=month_start, created_at__lt=month_end)
        monthly_data.append({
            'month': month_start.strftime('%b %Y'),
            'created': month_mas.count(),
            'approved': month_mas.filter(status='approved').count(),
            'rejected': month_mas.filter(status='rejected').count()
        })
    
    # 8. Reviewer performance (average time from creation to review)
    reviewers = CustomUser.objects.filter(
        user_type='Team',
        reviewed_mas__isnull=False
    ).distinct()
    
    reviewer_stats = []
    for reviewer in reviewers:
        reviewed = MAS.objects.filter(reviewer=reviewer, review_date__isnull=False)
        if reviewed.exists():
            avg_review_time = sum([
                (m.review_date - m.created_at).total_seconds() 
                for m in reviewed
            ]) / reviewed.count()
            reviewer_stats.append({
                'name': reviewer.username,
                'count': reviewed.count(),
                'avg_hours': round(avg_review_time / 3600, 1)
            })
    reviewer_stats = sorted(reviewer_stats, key=lambda x: x['count'], reverse=True)[:10]
    
    # 9. Approver performance (average time from review to approval)
    approvers = CustomUser.objects.filter(
        user_type='Team',
        approved_mas__isnull=False
    ).distinct()
    
    approver_stats = []
    for approver in approvers:
        approved = MAS.objects.filter(
            approver=approver, 
            approval_date__isnull=False,
            status='approved'
        )
        if approved.exists():
            avg_approval_time = sum([
                (m.approval_date - m.review_date).total_seconds() if m.review_date else 0
                for m in approved if m.review_date
            ])
            count_with_review = sum([1 for m in approved if m.review_date])
            if count_with_review > 0:
                avg_approval_time = avg_approval_time / count_with_review
                approver_stats.append({
                    'name': approver.username,
                    'count': approved.count(),
                    'avg_hours': round(avg_approval_time / 3600, 1)
                })
    approver_stats = sorted(approver_stats, key=lambda x: x['count'], reverse=True)[:10]
    
    # 10. Status distribution
    status_distribution = {
        'Pending Review': all_mas.filter(status='pending_review').count(),
        'Pending Approval': all_mas.filter(status='pending_approval').count(),
        'Approved': approved_mas,
        'Rejected': rejected_mas,
        'Revision Requested': revision_requested_mas
    }
    
    context = {
        'total_mas': total_mas,
        'approved_mas': approved_mas,
        'pending_mas': pending_mas,
        'rejected_mas': rejected_mas,
        'revision_requested_mas': revision_requested_mas,
        'mas_with_revisions': mas_with_revisions,
        'total_revisions': total_revisions,
        'avg_approval_time': avg_approval_time,
        'project_stats': project_stats,
        'item_stats': item_stats,
        'vendor_stats': vendor_stats,
        'monthly_data': monthly_data,
        'reviewer_stats': reviewer_stats,
        'approver_stats': approver_stats,
        'status_distribution': status_distribution,
        # New metrics
        'mas_processed_total': mas_processed_total,
        'mas_processed_last_quarter': mas_processed_last_quarter,
        'mas_processed_last_30_days': mas_processed_last_30_days,
        'open_mas_count': open_mas_count,
        'reviewer_summary': reviewer_summary,
        'service_wise_open': service_wise_open,
        'service_wise_tat': service_wise_tat,
    }
    
    return render(request, 'accounts/analytics_dashboard.html', context)
