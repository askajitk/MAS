from django.urls import path
from . import views

app_name = 'mas_sheets'

urlpatterns = [
    path('create/', views.mas_create, name='mas_create'),
    path('edit/<int:pk>/', views.mas_edit, name='mas_edit'),
    path('list/', views.mas_list, name='mas_list'),
    path('review/<int:pk>/', views.review_mas, name='review_mas'),
    path('approve/<int:pk>/', views.approve_mas, name='approve_mas'),
    path('revision/<int:pk>/', views.mas_revision, name='mas_revision'),
    # AJAX URLs
    path('ajax/load-buildings/', views.load_buildings, name='ajax_load_buildings'),
    path('ajax/load-services/', views.load_services, name='ajax_load_services'),
    path('ajax/load-items/', views.load_items, name='ajax_load_items'),
    path('ajax/load-makes/', views.load_makes, name='ajax_load_makes'),
]