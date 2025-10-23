from django.urls import path
from . import views

urlpatterns = [
    path('', views.project_list, name='project_list'),
    path('create/', views.project_create, name='project_create'),
    path('<int:pk>/', views.project_detail, name='project_detail'),
    path('<int:pk>/edit/', views.project_edit, name='project_edit'),
    path('<int:project_pk>/buildings/add/', views.building_create, name='building_create'),
    path('<int:project_pk>/team/add/', views.team_member_add, name='team_member_add'),
    path('<int:project_pk>/vendors/add/', views.vendor_add, name='vendor_add'),
    path('search/', views.search_projects, name='search_projects'),
    path('buildings/search/', views.search_buildings, name='search_buildings'),
    path('users/search/', views.search_users, name='search_users'),
]