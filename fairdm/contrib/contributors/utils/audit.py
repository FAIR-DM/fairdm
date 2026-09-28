"""Audit logging for claiming events."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from fairdm.contrib.contributors.models import Person


def log_claiming_event(
    method: str,
    source: Person | None,
    target: Person | None,
    initiated_by: Person | None = None,
    ip_address: str | None = None,
    success: bool = True,
    failure_reason: str = "",
    details: dict[str, Any] | None = None,
):
    """Write an immutable audit record for a claiming event.

    Args:
        method: A ``ClaimMethod`` value such as ``orcid``, ``email`` or ``token``.
        source: The unclaimed person being claimed, if known.
        target: The resulting claimed person, or None when the claim failed before linking.
        initiated_by: The admin who initiated an admin-driven claim.
        ip_address: The requester's IP address.
        success: Whether the claim succeeded.
        failure_reason: Why the claim failed.
        details: JSON-serialisable metadata about the event.

    Returns:
        The new audit record.
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
