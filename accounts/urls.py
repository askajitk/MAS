from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('check-username/', views.check_username, name='check_username'),
    path('password_change/', auth_views.PasswordChangeView.as_view(), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(), name='password_change_done'),
    
    # User management (Admin only)
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:pk>/delete/', views.user_delete, name='user_delete'),
    path('projects/<int:project_pk>/users/', views.project_users, name='project_users'),
    # Unassign users from project (Admin only)
    path('projects/<int:project_pk>/users/<int:user_pk>/unassign/team/', views.unassign_team_member, name='unassign_team_member'),
    path('projects/<int:project_pk>/users/<int:user_pk>/unassign/vendor/', views.unassign_vendor, name='unassign_vendor'),
]