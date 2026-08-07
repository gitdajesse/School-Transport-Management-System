from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, Parent, Bus, Student, Assistant, Attendance, Notification, RouteAssignment

# Register your models here.
admin.site.register(Parent)
admin.site.register(Bus)
admin.site.register(Student)
admin.site.register(Assistant)
admin.site.register(Attendance)
admin.site.register(Notification)
admin.site.register(RouteAssignment)

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'user_type', 'phone_number', 'is_active')
    list_filter = ('user_type', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('user_type', 'phone_number')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Custom Fields', {'fields': ('user_type', 'phone_number')}),
    )

admin.site.register(User, CustomUserAdmin)


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'status', 'pickup_time', 'dropoff_time', 'bus')
    list_filter = ('status', 'date', 'bus')
    search_fields = ('student__name', 'bus__registration')
    readonly_fields = ('recorded_at', 'updated_at')
    fieldsets = (
        ('Student Information', {
            'fields': ('student', 'bus', 'assistant')
        }),
        ('Status Details', {
            'fields': ('status', 'pickup_time', 'dropoff_time', 'notes')
        }),
        ('Audit Information', {
            'fields': ('recorded_at', 'updated_at', 'recorded_by', 'last_modified_by'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('student', 'bus', 'assistant')
