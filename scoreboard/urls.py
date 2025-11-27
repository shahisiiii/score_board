# ============================================
# FILE: scoreboard/urls.py
# ============================================

from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register-admin/', views.register_admin_view, name='register_admin'),
    path('register-user/', views.register_user_view, name='register_user'),
    
    # Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # Members
    path('members/', views.member_list_view, name='member_list'),
    path('members/create/', views.member_create_view, name='member_create'),
    path('members/<int:pk>/edit/', views.member_edit_view, name='member_edit'),
    path('members/<int:pk>/delete/', views.member_delete_view, name='member_delete'),
    
    # Score Entries
    path('scores/', views.score_entry_list_view, name='score_entry_list'),
    path('scores/create/', views.score_entry_create_view, name='score_entry_create'),
    path('scores/<int:pk>/', views.score_entry_detail_view, name='score_entry_detail'),
    path('scores/<int:pk>/download/', views.generate_scoreboard_image, name='generate_scoreboard'),
    path("scoreboard/overall/download/", views.generate_overall_scoreboard_image, name="overall_scoreboard_download"),

]
