"""Corrects JobSpy's `is_remote` flag using ground truth already present in
the scraped description text.

Found while manually verifying live search results: JobSpy's `is_remote`
flagged several postings "remote" that were actually onsite or hybrid.
Indeed appends a literal `Work Location: <value>` line to every posting's
description ("In person" / "Remote" / "Hybrid remote in <city>") - that
field is authoritative and already sitting in `Job.description`, so this
never needs a second network call.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

_WORK_LOCATION_PATTERN = re.compile(r"work location:\s*([^\n\r]+)", re.IGNORECASE)


@dataclass
class RemoteVerification:
    remote_status: str
    source: str  # "indeed_work_location_field" | "unchanged"
    changed: bool


def verify_remote_status(description: Optional[str], current_status: str) -> RemoteVerification:
    """Checks `description` for Indeed's "Work Location:" field and returns
    the corrected status if present. Falls back to `current_status`
    unchanged if the field isn't found (e.g. non-Indeed sources)."""
    match = _WORK_LOCATION_PATTERN.search(description or "")
    if not match:
        return RemoteVerification(remote_status=current_status, source="unchanged", changed=False)

    value = match.group(1).strip().lower()
    if "hybrid" in value:
        corrected = "hybrid"
    elif "remote" in value:
        corrected = "remote"
    elif "in person" in value or "on-site" in value or "onsite" in value:
        corrected = "onsite"
    else:
        return RemoteVerification(remote_status=current_status, source="unchanged", changed=False)

    return RemoteVerification(
        remote_status=corrected,
        source="indeed_work_location_field",
        changed=corrected != current_status,
    )
