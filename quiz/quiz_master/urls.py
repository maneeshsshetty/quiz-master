from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('leaderboard/', views.admin_leaderboard, name='admin_leaderboard'),
    path('users/', views.admin_users, name='admin_users'),
    path('create-user/', views.admin_create_user, name='admin_create_user'),
    path('activate/<uidb64>/<token>/', views.activate_account, name='activate_account'),
    path('take-quiz/<int:quiz_id>/', views.take_quiz, name='take_quiz'),
    path('results/', views.admin_results, name='admin_results'),
    path('result-detail/<int:result_id>/', views.view_result_detail, name='result_detail'),
    path('profile/', views.edit_profile, name='edit_profile'),
    path('login/', views.CustomLoginView.as_view(template_name='quiz_master/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
]
