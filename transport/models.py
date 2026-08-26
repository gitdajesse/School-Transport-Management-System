from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta

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
        ('late', 'Late'),
        ('pending', 'Pending')
    )

    # Core fields
    student = models.ForeignKey(Student, on_delete = models.CASCADE, related_name = 'attendance_records')
    assistant = models.ForeignKey(Assistant, on_delete = models.SET_NULL, null = True, related_name = 'attendance_records')
    bus = models.ForeignKey(Bus, on_delete = models.CASCADE, related_name = 'attendance_records')

    # Date and time fields
    date = models.DateField(auto_now_add = True)
    pickup_time = models.DateTimeField(null = True, blank = True)
    dropoff_time = models.DateTimeField(null = True, blank = True)
    recorded_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    # Status and additional info
    status = models.CharField(max_length = 20, choices = ATTENDANCE_STATUS, default = 'pending')
    notes = models.TextField(blank = True, null = True)

    # Track who made changes
    recorded_by = models.ForeignKey('User', on_delete = models.SET_NULL, null = True, related_name = 'recorded_attendances')
    last_modified_by = models.ForeignKey('User', on_delete = models.SET_NULL, null = True, related_name = 'modified_attendances')

    class Meta:
        unique_together = ['student', 'date']
        ordering = ['-date', '-recorded_at']

    def __str__(self):
        return f"{self.student.name} - {self.date} - {self.status}"

    def is_picked_up(self):
        return self.status in ['picked_up', 'dropped_off']

    def is_dropped_off(self):
        return self.status == 'dropped_off'

    def is_absent(self):
        return self.status == 'absent'

    def is_late(self):
        return self.status == 'late'

    def get_time_since_pickup(self):
        """ Return time since pickup in minutes """
        if self.pickup_time:
            delta = timezone.now() - self.pickup_time
            return int(delta.total_seconds() / 60)
        return None

    def get_formatted_timeline(self):
        """ Return a formatted timeline of the attendance """
        timeline = []

        if self.pickup_time:
            timeline.append({
                'event': 'Picked Up',
                'time': self.pickup_time,
                'formatted_time': self.pickup_time.strftime('%I:%M %p')
            })
        if self.dropoff_time:
            timeline.append({
                'event': 'Dropped Off',
                'time': self.dropoff_time,
                'formatted_time': self.dropoff_time.strftime('%I:%M %p')
            })
        return timeline

    def mark_picked_up(self, user = None, notes = None):
        """ Mark student as picked up """
        self.status = 'picked_up'
        self.pickup_time = timezone.now()

        if notes:
            self.notes = notes
        if user:
            self.recorded_by = user
            self.last_modified_by = user
        self.save()
        return self

    def mark_dropped_off(self, user = None, notes = None):
        """ Mark student as dropped off """
        if not self.pickup_time:
            raise ValueError("Cannot drop off a student who wasn't picked up")
        self.status = 'dropped_off'
        self.dropoff_time = timezone.now()

        if notes:
            self.notes = notes
        if user:
            self.last_modified_by = user
        self.save()
        return self

    def mark_absent(self, user = None, notes = None):
        """ Mark student as absent """
        self.status = 'absent'

        if notes:
            self.notes = notes
        if user:
            self.recorded_by = user
            self.last_modified_by = user
        self.save()
        return self

    def mark_late(self, user = None, notes = None):
        """ Mark student as late """
        self.status = 'late'
        self.pickup_time = timezone.now()

        if notes:
            self.notes = notes
        if user:
            self.recorded_by = user
            self.last_modified_by = user
        self.save()
        return self


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('attendance', 'Attendance Update'),
        ('fee', 'Fee Reminder'),
        ('route', 'Route Change'),
        ('bus', 'Bus Assignment'),
        ('system', 'System Alert'),
        ('general', 'General Announcement'),
    )

    DELIVERY_METHODS = (
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('app', 'In-App'),
    )

    is_automatic = models.BooleanField(default = True, help_text = "Was this triggered automatically by the system?")
    recipient = models.ForeignKey(User, on_delete = models.CASCADE, related_name = 'notifications')
    notification_type = models.CharField(max_length = 20, choices = NOTIFICATION_TYPES)
    delivery_method = models.CharField(max_length = 10, choices = DELIVERY_METHODS)
    subject = models.CharField(max_length = 200)
    message = models.TextField()
    read = models.BooleanField(default = False)
    delivered = models.BooleanField(default = False)
    created_at = models.DateTimeField(auto_now_add = True)
    sent_at = models.DateTimeField(null = True, blank = True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.recipient.username} - {self.subject[:50]}"

    def mark_as_read(self):
        self.read = True
        self.save()

    def mark_as_delivered(self):
        self.delivered = True
        self.sent_at = timezone.now()
        self.save()


class RouteAssignment(models.Model):
    student = models.ForeignKey(Student, on_delete = models.CASCADE)
    bus = models.ForeignKey(Bus, on_delete = models.CASCADE)
    assigned_date = models.DateTimeField(auto_now_add = True)
    is_active = models.BooleanField(default = True)

    class Meta:
        unique_together = ['student', 'bus', 'assigned_date']

    def __str__(self):
        return f"{self.student.name} assigned to {self.bus.registration}"


class Route(models.Model):
    name = models.CharField(max_length = 100, unique = True)
    description = models.TextField(blank = True)
    is_active = models.BooleanField(default = True)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    def __str__(self):
        return self.name

    def get_stops_in_order(self):
        return self.stops.order_by('order')

    def get_student_count(self):
        return Student.objects.filter(bus__route_name = self.name, is_active = True).count()


class Stop(models.Model):
    route = models.ForeignKey(Route, on_delete = models.CASCADE, related_name = 'stops')
    name = models.CharField(max_length = 200)
    address = models.TextField()
    order = models.IntegerField()
    pickup_time = models.TimeField(null = True, blank = True)
    dropoff_time = models.TimeField(null = True, blank = True)
    is_active = models.BooleanField(default = True)

    class Meta:
        ordering = ['order']
        unique_together = ['route', 'order']

    def __str__(self):
        return f"{self.route.name} - Stop {self.order}: {self.name}"


class Fee(models.Model):
    """ Fee record for a student for a specific term """

    TERM_CHOICES = (
        ('January', 'January Term'),
        ('April', 'April Term'),
        ('August', 'August Term'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('waived', 'Waived'),
    )

    student = models.ForeignKey(Student, on_delete = models.CASCADE, related_name = 'fees')
    term = models.CharField(max_length = 20, choices = TERM_CHOICES)
    year = models.IntegerField()
    amount = models.DecimalField(max_digits = 10, decimal_places = 2)
    due_date = models.DateField()

    status = models.CharField(max_length = 20, choices = STATUS_CHOICES, default = 'pending')
    paid_amount = models.DecimalField(max_digits = 10, decimal_places = 2, default = 0.00)
    balance = models.DecimalField(max_digits = 10, decimal_places = 2, default = 0.00)

    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    paid_at = models.DateTimeField(null = True, blank = True)

    notes = models.TextField(blank = True, null = True)

    class Meta:
        unique_together = ['student', 'term', 'year']
        ordering = ['-year', '-term']
        indexes = [
            models.Index(fields = ['student', 'status']),
            models.Index(fields = ['due_date', 'status'])
        ]

    def __str__(self):
        return f"{self.student.name} - {self.term} {self.year} - {self.status}"

    def save(self, *args, **kwargs):
        """ Calculate balance before saving """
        self.balance = self.amount - self.paid_amount
        if self.balance <= 0 and self.paid_amount > 0:
            self.status = 'paid'
            if not self.paid_at:
                self.paid_at = timezone.now()
        elif self.paid_amount > 0 and self.paid_amount < self.amount:
            self.status = 'partial'
        elif self.due_date and timezone.now().date() > self.due_date and self.paid_amount == 0:
            self.status = 'overdue'
        super().save(*args, **kwargs)

    def is_paid(self):
        return self.status == 'paid'

    def is_overdue(self):
        return self.status == 'overdue' or (self.due_date and timezone.now().date() > self.due_date and not self.is_paid())

    def get_balance_due(self):
        return self.amount - self.paid_amount

    def get_payment_percentage(self):
        if self.amount > 0:
            return (self.paid_amount / self.amount) * 100
        return 0


class Payment(models.Model):
    """ Payment record for a fee """

    PAYMENT_METHODS = (
        ('mpesa', 'M-PESA'),
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('cheque', 'Cheque'),
        ('other', 'Other'),
    )

    fee = models.ForeignKey(Fee, on_delete = models.CASCADE, related_name = 'payments')
    amount = models.DecimalField(max_digits = 10, decimal_places = 2)
    payment_method = models.CharField(max_length = 20, choices = PAYMENT_METHODS)

    reference_number = models.CharField(max_length = 100, blank = True, null = True)
    payment_date = models.DateTimeField(default = timezone.now)
    recorded_by = models.ForeignKey('User', on_delete = models.SET_NULL, null = True, related_name = 'recorded_payments')

    notes = models.TextField(blank = True, null = True)

    created_at = models.DateTimeField(auto_now_add = True)

    class Meta:
        ordering = ['-payment_date']

    def __str__(self):
        return f"Payment of {self.fee.student.name} - {self.amount} ({self.payment_method})"
