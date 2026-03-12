from datetime import date
from typing import Any

ACTIVE_KEYWORDS = ["until"]


def _field_is_active(value: Any) -> bool:
    """
    Return True if a DateOrNote field value indicates active support.

    If a date is present it takes priority, returns True if today or in the
    future, False if in the past, regardless of notes.
    If only notes are present, returns True if they contain an active keyword
    (e.g. 'until').
    """

    if not isinstance(value, dict):
        return False

    date_value = value.get("date")
    notes_value = value.get("notes")

    if date_value:
        try:
            lifecycle_date = date.fromisoformat(date_value)
        except (TypeError, ValueError):
            return False

        return lifecycle_date >= date.today()

    if notes_value:
        normalized_notes = notes_value.lower()
        return any(keyword in normalized_notes for keyword in ACTIVE_KEYWORDS)

    return False


def is_version_active(version: Any) -> bool:
    """Return True if any lifecycle field indicates this version is active."""

    lifecycle_fields = [
        version.supported,
        version.pro_supported,
        version.legacy_supported,
    ]

    return any(
        _field_is_active(field_value) for field_value in lifecycle_fields
    )


def is_product_active(product: Any) -> bool:
    """Return True if the product has at least one active version."""

    versions = [
        version
        for deployment in product.deployments
        for version in deployment.versions
    ]

    if not versions:
        return True

    return any(is_version_active(version) for version in versions)
