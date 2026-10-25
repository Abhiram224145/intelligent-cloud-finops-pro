
from datetime import datetime, timezone


def create_notification(resource_id, message, severity="Warning"):
    """Create an in-app notification record."""

    return {
        "resource_id": str(resource_id),
        "message": str(message),
        "severity": severity,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "Unread",
    }
