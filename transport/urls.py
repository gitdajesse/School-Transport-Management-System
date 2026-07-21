from django.urls import path
from . import views

urlpatterns = [
    # Authentication URLs
    path('', views.index, name = 'index'),
    path('register/', views.register, name = 'register'),
    path('login/', views.login_view, name = 'login'),
    path('logout/', views.logout_view, name = 'logout'),

    # Dashboard URLs
    path('parent-dashboard/', views.parent_dashboard, name = 'parent_dashboard'),
    path('assistant-dashboard/', views.assistant_dashboard, name = 'assistant_dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name = 'admin_dashboard'),

    # Student management URLs
    path('manage-system/', views.manage_system, name = 'manage_system'),
    path('students/', views.student_list, name = 'student_list'),
    path('students/edit/<int:student_id>/', views.edit_student, name = 'edit_student'),
    path('students/deactivate/<int:student_id>/', views.deactivate_student, name = 'deactivate_student'),
    path('students/reactivate/<int:student_id>/', views.reactivate_student, name = 'reactivate_student'),

    # Bus management URLs
    path('buses/', views.bus_list, name = 'bus_list'),
    path('buses/edit/<int:bus_id>', views.edit_bus, name = 'edit_bus'),
    path('buses/deactivate/<int:bus_id>', views.deactivate_bus, name = 'deactivate_bus'),
    path('buses/reactivate/<int:bus_id>', views.reactivate_bus, name = 'reactivate_bus'),
]
