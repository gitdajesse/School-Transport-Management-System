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
    path('buses/edit/<int:bus_id>/', views.edit_bus, name = 'edit_bus'),
    path('buses/deactivate/<int:bus_id>/', views.deactivate_bus, name = 'deactivate_bus'),
    path('buses/reactivate/<int:bus_id>/', views.reactivate_bus, name = 'reactivate_bus'),
    path('buses/detail/<int:bus_id>/', views.bus_detail, name = 'bus_detail'),

    # Route management URLs
    path('routes/', views.route_list, name = 'route_list'),
    path('routes/detail/<int:route_id>/', views.route_detail, name = 'route_detail'),
    path('routes/edit/<int:route_id>/', views.edit_route, name = 'edit_route'),
    path('routes/deactivate/<int:route_id>/', views.deactivate_route, name = 'deactivate_route'),
    path('routes/reactivate/<int:route_id>/', views.reactivate_route, name = 'reactivate_route'),

    # Stop management URLs
    path('routes/add-stop/<int:route_id>/', views.add_stop, name = 'add_stop'),
    path('stops/edit/<int:stop_id>/', views.edit_stop, name = 'edit_stop'),
    path('stops/delete/<int:stop_id>/', views.delete_stop, name = 'delete_stop'),

    # Notification management URLs
    path('notifications/', views.notification_list, name = 'notification_list'),
    path('notifications/detail/<int:notification_id>/', views.notification_detail, name = 'notification_detail'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name = 'mark_all_notifications_read'),

    # Attendance managemnt URLs
    path('manage-attendance/', views.manage_attendance, name = 'manage_attendance'),
    path('attendance/assistant/', views.assistant_attendance, name = 'assistant_attendance'),
]
