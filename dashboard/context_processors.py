# Enable postponed evaluation of type hints
from __future__ import annotations

# Import helper function to get the currently logged-in user
from dashboard.auth import get_current_actor

# Import the Notification model
from dashboard.models import Notification


# Make logged-in user information available to all templates
def current_user(request):

    # Get the current user's role and object
    role, actor = get_current_actor(request)

    # Initialize unread notification count
    unread_count = 0

    # Initialize recent notifications list
    recent_notifications = []

    # Continue only if a user is logged in
    if actor is not None:

        # Get notifications for the logged-in customer
        if role == "customer":
            qs = Notification.objects.filter(
                audience=Notification.Audience.CUSTOMER,
                customer=actor
            )

        # Get notifications for the logged-in employee or manager
        else:
            qs = Notification.objects.filter(
                audience=Notification.Audience.EMPLOYEE,
                employee=actor
            )

        # Count unread notifications
        unread_count = qs.filter(is_read=False).count()

        # Get the latest six notifications
        recent_notifications = list(
            qs.order_by("-created_at")[:6]
        )

    # Return data that will be available in every template
    return {
        "current_user": actor,
        "current_role": role,
        "unread_notifications": unread_count,
        "recent_notifications": recent_notifications,
    }
