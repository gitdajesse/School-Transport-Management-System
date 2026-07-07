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
