from django import template
from transport.models import Notification

register = template.Library()


@register.simple_tag(takes_context=True)
def unread_notification_count(context):
    """Get unread count for current user"""
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return 0
    return Notification.objects.filter(recipient=request.user, read=False).count()