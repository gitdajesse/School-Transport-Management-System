from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name = 'index'),
    path('register/', views.register, name = 'register'),
    path('login/', views.login, name = 'login'),
    path('logout/', views.logout, name = 'logout'),
    path('parent-dashboard/', views.parent_dashboard, name = 'parent_dashboard'),
    path('assistant-dashboard/', views.assistant_dashboard, name = 'assistant_dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name = 'admin_dashboard')
]
