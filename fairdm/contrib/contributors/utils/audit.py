from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from fairdm.contrib.contributors.models import Person


def log_claiming_event(
    method: str,
    source: "Person | None",
    target: "Person | None",
    initiated_by: "Person | None" = None,
    ip_address: str | None = None,
    success: bool = True,
    failure_reason: str = "",
    details: dict[str, Any] | None = None,
):
    """Create an immutable ClaimingAuditLog record for a claiming event.

    Args:
        method: One of ClaimMethod choices (e.g., "orcid", "email", "token").
        source: The unclaimed Person being claimed (or None if not known).
        target: The resulting claimed Person (or None if claim failed before linking).
        initiated_by: Admin who initiated (for admin-driven claims), or None.
        ip_address: Request IP address for security auditing, or None.
        success: True if the claim succeeded, False otherwise.
        failure_reason: Short description of why the claim failed (if success=False).
        details: Arbitrary JSON-serialisable metadata about the event.

    Returns:
        ClaimingAuditLog: The newly created (immutable) audit record.
    """
    from fairdm.contrib.contributors.models import ClaimingAuditLog

    return ClaimingAuditLog.objects.create(
        method=method,
        source_person=source,
        target_person=target,
        initiated_by=initiated_by,
        ip_address=ip_address,
        success=success,
        failure_reason=failure_reason,
        details=details or {},
    )
