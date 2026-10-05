"""
Central notification dispatch system.
This is the single source of truth for sending notifications.
"""
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import Notification, NotificationPreference


class NotificationDispatcher:
    """
    Central dispatcher for all notifications.
    Decides which channel to use based on user preferences.
    """

    @staticmethod
    def dispatch(
        recipient,
        notification_type,
        subject,
        message,
        priority='normal',
        related_student=None,
        related_fee=None,
        related_attendance=None,
        action_url=None,
        action_text=None,
        force_delivery=False,
    ):
        """
        Main dispatch method.
        Creates in-app notification AND sends via enabled channels.
        """
        # Get user preferences
        prefs, _ = NotificationPreference.objects.get_or_create(user=recipient)

        # Check if user wants this type of notification
        if not force_delivery and not prefs.should_send(notification_type):
            print(f"⚠️ User {recipient.username} opted out of {notification_type}")
            return None

        # Check quiet hours
        if prefs.is_quiet_hours() and priority not in ['urgent', 'high']:
            print(f"⚠️ Quiet hours for {recipient.username}, skipping")
            return None

        # Create in-app notification (always created unless opted out)
        notification = None
        if prefs.in_app_enabled or force_delivery:
            notification = Notification.objects.create(
                recipient=recipient,
                notification_type=notification_type,
                delivery_method='app',
                priority=priority,
                subject=subject,
                message=message,
                related_student=related_student,
                related_fee=related_fee,
                related_attendance=related_attendance,
                action_url=action_url,
                action_text=action_text,
                is_automatic=True,
                delivered=True,
            )
            notification.mark_as_delivered()

        # Email delivery
        if prefs.email_enabled and recipient.email:
            NotificationDispatcher._send_email(recipient, subject, message, notification)

        # SMS delivery (placeholder - integrate with your SMS provider)
        if prefs.sms_enabled and hasattr(recipient, 'phone_number'):
            NotificationDispatcher._send_sms(recipient, subject, message, notification)

        return notification

    @staticmethod
    def _send_email(recipient, subject, message, notification=None):
        """Send notification via email"""
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient.email],
                fail_silently=False,
            )
            print(f"✅ Email sent to {recipient.email}")
            return True
        except Exception as e:
            error_msg = f"Email delivery failed: {str(e)}"
            print(f"❌ {error_msg}")
            if notification:
                notification.mark_delivery_error(error_msg)
            return False

    @staticmethod
    def _send_sms(recipient, subject, message, notification=None):
        """
        Send notification via SMS.
        Placeholder - integrate with Twilio, Africa's Talking, etc.
        """
        try:
            # Example with a placeholder
            # from twilio.rest import Client
            # client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            # client.messages.create(to=recipient.phone_number, from_=settings.TWILIO_PHONE, body=message[:160])

            print(f"📱 SMS placeholder: would send to {recipient.phone_number}")
            print(f"   Message: {message[:100]}")
            return True
        except Exception as e:
            error_msg = f"SMS delivery failed: {str(e)}"
            print(f"❌ {error_msg}")
            if notification:
                notification.mark_delivery_error(error_msg)
            return False

    @staticmethod
    def dispatch_bulk(recipients_and_messages):
        """
        Dispatch multiple notifications.
        recipients_and_messages: list of dicts with keys:
            recipient, notification_type, subject, message, priority, etc.
        """
        results = []
        for item in recipients_and_messages:
            result = NotificationDispatcher.dispatch(**item)
            results.append(result)
        return results


# ============================================================
# Specific Notification Helpers
# ============================================================

def notify_parent_student_picked_up(student, attendance):
    """Notify parent when child is picked up"""
    parent = student.parent
    if not parent or not parent.user:
        return None

    return NotificationDispatcher.dispatch(
        recipient=parent.user,
        notification_type='attendance',
        subject=f'✅ {student.name} Picked Up',
        message=f"""
Dear Parent,

Your child {student.name} has been picked up.

Details:
- Time: {attendance.pickup_time.strftime('%I:%M %p')}
- Bus: {student.bus.registration}
- Route: {student.bus.route_name}

Your child is on the way to school.
        """,
        priority='normal',
        related_student=student,
        related_attendance=attendance,
        action_url=f'/attendance/detail/{attendance.id}/',
        action_text='View Attendance',
    )


def notify_parent_student_dropped_off(student, attendance):
    """Notify parent when child arrives at school"""
    parent = student.parent
    if not parent or not parent.user:
        return None

    return NotificationDispatcher.dispatch(
        recipient=parent.user,
        notification_type='attendance',
        subject=f'🏫 {student.name} Arrived at School',
        message=f"""
Dear Parent,

Your child {student.name} has arrived at school.

Details:
- Time: {attendance.dropoff_time.strftime('%I:%M %p')}
- Bus: {student.bus.registration}

Have a great day!
        """,
        priority='normal',
        related_student=student,
        related_attendance=attendance,
        action_url=f'/attendance/detail/{attendance.id}/',
        action_text='View Attendance',
    )


def notify_parent_student_absent(student, attendance):
    """Notify parent when child is marked absent"""
    parent = student.parent
    if not parent or not parent.user:
        return None

    return NotificationDispatcher.dispatch(
        recipient=parent.user,
        notification_type='attendance',
        subject=f'❌ {student.name} Marked Absent',
        message=f"""
Dear Parent,

Your child {student.name} was marked absent today ({attendance.date}).

If this is unexpected, please contact the school administration.

Thank you.
        """,
        priority='high',
        related_student=student,
        related_attendance=attendance,
    )


def notify_parent_student_late(student, attendance):
    """Notify parent when child is marked late"""
    parent = student.parent
    if not parent or not parent.user:
        return None

    return NotificationDispatcher.dispatch(
        recipient=parent.user,
        notification_type='attendance',
        subject=f'⏰ {student.name} Marked Late',
        message=f"""
Dear Parent,

Your child {student.name} was marked late today.

Time: {attendance.pickup_time.strftime('%I:%M %p')}

Please ensure your child is ready earlier tomorrow.

Thank you.
        """,
        priority='normal',
        related_student=student,
        related_attendance=attendance,
    )


def notify_parent_new_fee(fee):
    """Notify parent when a new fee is generated"""
    parent = fee.student.parent
    if not parent or not parent.user:
        return None

    return NotificationDispatcher.dispatch(
        recipient=parent.user,
        notification_type='fee',
        subject=f'📋 New Transport Fee - {fee.student.name}',
        message=f"""
Dear Parent,

A new transport fee is now available for {fee.student.name}.

Details:
- Term: {fee.term} {fee.year}
- Amount: ${fee.amount}
- Due Date: {fee.due_date.strftime('%B %d, %Y')}

Please make your payment by the due date to avoid service interruption.

Thank you.
        """,
        priority='normal',
        related_student=fee.student,
        related_fee=fee,
        action_url=f'/fees/detail/{fee.id}/',
        action_text='View Fee Details',
    )


def notify_parent_fee_overdue(fee):
    """Notify parent when a fee becomes overdue"""
    parent = fee.student.parent
    if not parent or not parent.user:
        return None

    days_overdue = (timezone.now().date() - fee.due_date).days

    return NotificationDispatcher.dispatch(
        recipient=parent.user,
        notification_type='fee',
        subject=f'❌ Overdue Fee - {fee.student.name}',
        message=f"""
Dear Parent,

The transport fee for {fee.student.name} is now overdue.

Details:
- Term: {fee.term} {fee.year}
- Amount: ${fee.amount}
- Due Date: {fee.due_date.strftime('%B %d, %Y')}
- Days Overdue: {days_overdue} days

IMPORTANT: Your child will not be picked up until this fee is paid.

Please make your payment immediately.

Thank you.
        """,
        priority='urgent',
        related_student=fee.student,
        related_fee=fee,
        action_url=f'/fees/pay/{fee.id}/',
        action_text='Pay Now',
    )


def notify_parent_payment_received(fee, payment):
    """Notify parent when payment is recorded"""
    parent = fee.student.parent
    if not parent or not parent.user:
        return None

    return NotificationDispatcher.dispatch(
        recipient=parent.user,
        notification_type='fee',
        subject=f'✅ Payment Received - {fee.student.name}',
        message=f"""
Dear Parent,

We have received your payment of ${payment.amount} for {fee.student.name}.

Details:
- Amount: ${payment.amount}
- Method: {payment.get_payment_method_display()}
- Date: {payment.payment_date.strftime('%B %d, %Y')}
- Remaining Balance: ${fee.get_balance_due()}

Thank you for your payment.
        """,
        priority='normal',
        related_student=fee.student,
        related_fee=fee,
        action_url=f'/fees/detail/{fee.id}/',
        action_text='View Fee',
    )


def notify_parent_fee_waived(fee):
    """Notify parent when a fee is waived"""
    parent = fee.student.parent
    if not parent or not parent.user:
        return None

    return NotificationDispatcher.dispatch(
        recipient=parent.user,
        notification_type='fee',
        subject=f'✅ Fee Waived - {fee.student.name}',
        message=f"""
Dear Parent,

The transport fee for {fee.student.name} has been waived.

Details:
- Term: {fee.term} {fee.year}
- Amount: ${fee.amount}
- Reason: {fee.notes}

No payment is required.

Thank you.
        """,
        priority='normal',
        related_student=fee.student,
        related_fee=fee,
    )


def notify_parent_bus_change(student, old_bus, new_bus):
    """Notify parent when child's bus changes"""
    parent = student.parent
    if not parent or not parent.user:
        return None

    old_info = f"{old_bus.registration} ({old_bus.route_name})" if old_bus else "None"
    new_info = f"{new_bus.registration} ({new_bus.route_name})" if new_bus else "None"

    return NotificationDispatcher.dispatch(
        recipient=parent.user,
        notification_type='bus',
        subject=f'🚌 Bus Change - {student.name}',
        message=f"""
Dear Parent,

There has been a change to the transport bus for {student.name}.

Details:
- Previous Bus: {old_info}
- New Bus: {new_info}

Please update your records accordingly.

Thank you.
        """,
        priority='high',
        related_student=student,
    )


def notify_parent_route_change(student, route, change_description):
    """Notify parent when a route changes"""
    parent = student.parent
    if not parent or not parent.user:
        return None

    return NotificationDispatcher.dispatch(
        recipient=parent.user,
        notification_type='route',
        subject=f'🛣️ Route Change - {student.name}',
        message=f"""
Dear Parent,

There has been a change to the transport route for {student.name}.

Route: {route.name}
Change: {change_description}

Please check the updated schedule on your dashboard.

Thank you.
        """,
        priority='high',
        related_student=student,
    )


def notify_parent_student_deactivated(student):
    """Notify parent when student is deactivated"""
    parent = student.parent
    if not parent or not parent.user:
        return None

    return NotificationDispatcher.dispatch(
        recipient=parent.user,
        notification_type='student',
        subject=f'⚠️ Student Deactivated - {student.name}',
        message=f"""
Dear Parent,

Your child {student.name} has been deactivated from the transport system.

If this is unexpected, please contact the school administration.

Thank you.
        """,
        priority='urgent',
        related_student=student,
    )


def notify_assistant_bus_assignment(assistant, bus):
    """Notify assistant when assigned to a bus"""
    if not assistant.user:
        return None

    return NotificationDispatcher.dispatch(
        recipient=assistant.user,
        notification_type='bus',
        subject=f'🚌 Bus Assignment',
        message=f"""
Dear {assistant.name},

You have been assigned to the following bus:

- Bus: {bus.registration}
- Route: {bus.route_name}
- Driver: {bus.driver_name}
- Capacity: {bus.capacity}

Please report to the transport office for more details.
        """,
        priority='high',
    )
