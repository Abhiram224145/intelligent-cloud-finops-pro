
import json
from pathlib import Path
from datetime import datetime, timezone

APPROVAL_FILE = Path("approvals.json")


def load_approvals():
    if APPROVAL_FILE.exists():
        try:
            return json.loads(
                APPROVAL_FILE.read_text(encoding="utf-8")
            )
        except (json.JSONDecodeError, OSError):
            return []
    return []


def save_approvals(approvals):
    APPROVAL_FILE.write_text(
        json.dumps(approvals, indent=2),
        encoding="utf-8"
    )


def request_approval(resource_id, resource_type, reason):
    approvals = load_approvals()

    request = {
        "request_id": f"REQ-{len(approvals) + 1:04d}",
        "resource_id": str(resource_id),
        "resource_type": str(resource_type),
        "reason": str(reason),
        "status": "Pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "owner_response": ""
    }

    approvals.append(request)
    save_approvals(approvals)
    return request


def update_approval(request_id, decision, response=""):
    if decision not in ("Approved", "Rejected"):
        raise ValueError("Invalid approval decision.")

    approvals = load_approvals()

    for request in approvals:
        if request["request_id"] == request_id:
            if request["status"] != "Pending":
                return False

            request["status"] = decision
            request["owner_response"] = str(response)
            save_approvals(approvals)
            return True

    return False
