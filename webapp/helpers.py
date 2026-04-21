import re
from datetime import date
from types import SimpleNamespace
from typing import Any

ACTIVE_KEYWORDS = ["until"]


def slugify(name: str) -> str:
    """Generate a slug from a name.

    Lowercases the input, strips leading/trailing whitespace,
    replaces any sequence of non-alphanumeric characters with a hyphen,
    and strips leading/trailing hyphens from the result.
    """
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


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
        version.esm_pro_supported,
        version.break_bug_pro_supported,
        version.legacy_supported,
    ]

    return any(
        _field_is_active(field_value) for field_value in lifecycle_fields
    )


def filter_product_versions(
    product: Any,
    include_expired: bool = False,
    include_hidden: bool = False,
) -> Any:
    """
    Return a product-like object containing only visible
    deployments and versions.
    """

    filtered_deployments = []

    for deployment in product.deployments:
        filtered_deployment = filter_deployment_versions(
            deployment,
            include_expired=include_expired,
            include_hidden=include_hidden,
        )

        if filtered_deployment.versions:
            filtered_deployments.append(filtered_deployment)

    return SimpleNamespace(
        slug=product.slug,
        name=product.name,
        deployments=filtered_deployments,
    )


def filter_deployment_versions(
    deployment: Any,
    include_expired: bool = False,
    include_hidden: bool = False,
) -> Any:
    """Return a deployment-like object containing only visible versions."""

    versions = [
        version
        for version in deployment.versions
        if (include_expired or is_version_active(version))
        and (include_hidden or not version.is_hidden)
    ]

    return SimpleNamespace(
        slug=deployment.slug,
        parent_product=deployment.parent_product,
        name=deployment.name,
        artifact_type=deployment.artifact_type,
        versions=versions,
    )


def is_product_active(product: Any, include_hidden: bool = False) -> bool:
    """Return True if the product has at least one active, visible version."""

    versions = [
        version
        for deployment in product.deployments
        for version in deployment.versions
    ]

    if not versions:
        return True

    return any(
        is_version_active(version)
        and (include_hidden or not version.is_hidden)
        for version in versions
    )


def validate_dates_after_release(
    release_date: date,
    lifecycle_fields: dict,
) -> dict:
    """
    Return a field-level error if any lifecycle date falls before
    release_date. Only checks fields with concrete dates.
    """
    for field_name, field_value in lifecycle_fields.items():
        if not isinstance(field_value, dict):
            continue
        lifecycle_date_str = field_value.get("date")
        if not lifecycle_date_str:
            continue
        try:
            lifecycle_date = date.fromisoformat(lifecycle_date_str)
        except (TypeError, ValueError):
            continue
        if lifecycle_date < release_date:
            return {field_name: ["Must not be before release_date."]}
    return {}
