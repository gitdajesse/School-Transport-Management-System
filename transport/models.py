from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
class User(AbstractUser):
    # Automatically creates username, password and email field
    USER_TYPES = (
        ('admin', 'Admin'),
        ('parent', 'Parent'),
        ('assistant', 'Assistant'),
    )
    user_type = models.CharField(max_length = 20, choices = USER_TYPES)
    phone_number = models.CharField(max_length = 15)
    is_active = models.BooleanField(default = True)

    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name="transport_user_set",
        related_query_name="transport_user",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="transport_user_set",
        related_query_name="transport_user",
    )

    def __str__(self):
        return self.username


class Parent(models.Model):
    user = models.OneToOneField(User, on_delete = models.CASCADE, related_name = 'parent_profile')
    name = models.CharField(max_length = 200)
    email = models.EmailField()
    phone_number = models.CharField(max_length = 15)
    home_address = models.TextField()

    def __str__(self):
        return self.name


class Bus(models.Model):
    registration = models.CharField(max_length = 50, unique = True)
    driver_name = models.CharField(max_length = 200)
    capacity = models.IntegerField()
    route_name = models.CharField(max_length = 100)
    is_active = models.BooleanField(default = True)
    created_at = models.DateTimeField(auto_now_add = True)

    def __str__(self):
        return f"Bus {self.registration} - {self.route_name}"


class Student(models.Model):
    name = models.CharField(max_length = 200)
    grade = models.CharField(max_length = 20)
    parent = models.ForeignKey(Parent, on_delete = models.CASCADE, related_name = 'children')
    bus = models.ForeignKey(Bus, on_delete = models.CASCADE, related_name = 'students')
    pick_up_location = models.CharField(max_length = 200)
    drop_off_location = models.CharField(max_length = 200)
    emergency_contact = models.CharField(max_length = 200)
    created_at = models.DateTimeField(auto_now_add = True)
    is_active = models.BooleanField(default = True)

    def __str__(self):
        return self.name


class Assistant(models.Model):
    user = models.OneToOneField(User, on_delete = models.CASCADE, related_name = 'assistant_profile')
    name = models.CharField(max_length = 200)
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length = 15, blank = True, null = True)
    bus = models.ForeignKey(Bus, on_delete = models.SET_NULL, null = True, related_name = 'assistants')
    hire_date = models.DateTimeField(auto_now_add = True)
    is_active = models.BooleanField(default = True)

    def __str__(self):
        return self.name


class Attendance(models.Model):
    ATTENDANCE_STATUS = (
        ('picked_up', 'Picked Up'),
        ('dropped_off', 'Dropped Off'),
        ('absent', 'Absent'),
        ('late', 'Late')
    )
    student = models.ForeignKey(Student, on_delete = models.CASCADE, related_name = 'attendance_records')
    assistant = models.ForeignKey(Assistant, on_delete = models.SET_NULL, null = True)
    bus = models.ForeignKey(Bus, on_delete = models.CASCADE)
    date = models.DateTimeField(auto_now_add = True)
    pickup_time = models.DateTimeField(null = True, blank = True)
    dropoff_time = models.DateTimeField(null = True, blank = True)
    status = models.CharField(max_length = 20, choices = ATTENDANCE_STATUS)
    notes = models.TextField(blank = True)
    recorded_at = models.DateTimeField(auto_now_add = True)

    class Meta:
        unique_together = ['student', 'date']

    def __str__(self):
        return f"{self.student.name} - {self.date} - {self.status}"


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('attendance', 'Attendance Update'),
        ('fee', 'Fee Reminder'),
        ('route', 'Route Change'),
        ('system', 'System Alert'),
        ('general', 'General Announcement'),
    )

    DELIVERY_METHODS = (
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('app', 'In-App'),
    )

    recipient = models.ForeignKey(User, on_delete = models.CASCADE, related_name = 'notifications')
    notification_type = models.CharField(max_length = 20, choices = NOTIFICATION_TYPES)
    delivery_method = models.CharField(max_length = 10, choices = DELIVERY_METHODS)
    subject = models.CharField(max_length = 200)
    message = models.TextField()
    read = models.BooleanField(default = False)
    delivered = models.BooleanField(default = False)
    created_at = models.DateTimeField(auto_now_add = True)
    sent_at = models.DateTimeField(null = True, blank = True)

    def __str__(self):
        return f"{self.recipient.username} - {self.subject[:50]}"


class RouteAssignment(models.Model):
    student = models.ForeignKey(Student, on_delete = models.CASCADE)
    bus = models.ForeignKey(Bus, on_delete = models.CASCADE)
    assigned_date = models.DateTimeField(auto_now_add = True)
    is_active = models.BooleanField(default = True)

    class Meta:
        unique_together = ['student', 'bus', 'assigned_date']

    def __str__(self):
        return f"{self.student.name} assigned to {self.bus.registration}"

