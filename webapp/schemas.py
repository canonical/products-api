import re

from marshmallow import (
    Schema,
    ValidationError,
    fields,
    post_load,
    validates,
    validates_schema,
)
from marshmallow.validate import OneOf, Length

from webapp.constants import ARTIFACT_TYPES, ARCHITECTURES

_SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def _validate_slug_format(value: str) -> None:
    """Validate that a (non-empty) slug matches the allowed pattern.

    Raises ValidationError if the slug does not match.
    """
    if not _SLUG_RE.match(value):
        raise ValidationError(
            "Slug may only contain lowercase letters, digits, and "
            "hyphens, and may not start or end with a hyphen."
        )


class DateOrNoteSchema(Schema):
    """DateOrNote support lifecycle field."""

    date = fields.String(required=False, allow_none=True)
    notes = fields.String(required=False, allow_none=True)

    @validates_schema
    def validate_date_or_note(self, data, **kwargs):
        if not data.get("date") and not data.get("notes"):
            raise ValidationError(
                "At least one of 'date' or 'notes' must be provided."
            )


class CompatibleLTSSchema(Schema):
    """Ubuntu LTS compatibility information for a release."""

    version = fields.String(required=True)
    compatible_components = fields.List(
        fields.String(), required=True, allow_none=False
    )


class ProductSchema(Schema):
    """Schema for Product model."""

    name = fields.String(required=True)
    slug = fields.String(dump_only=True)
    deployments = fields.List(
        fields.Nested(lambda: DeploymentSchema()),
        required=True,
        allow_none=False,
    )


class DeploymentSchema(Schema):
    """Schema for Deployment model."""

    slug = fields.String(dump_only=True)
    parent_product = fields.String(dump_only=True)
    name = fields.String(required=True)
    artifact_type = fields.String(
        required=True, validate=OneOf(ARTIFACT_TYPES)
    )
    versions = fields.List(
        fields.Nested(lambda: VersionSchema()), dump_only=True
    )


class VersionSchema(Schema):
    """Schema for Version model."""

    parent_product = fields.String(dump_only=True)
    parent_deployment = fields.String(dump_only=True)
    release = fields.String(required=True)
    architecture = fields.List(
        fields.String(validate=OneOf(ARCHITECTURES)),
        required=True,
        allow_none=False,
        validate=Length(min=1),
    )
    release_date = fields.Nested(DateOrNoteSchema, required=True)
    supported = fields.Nested(DateOrNoteSchema, required=True)
    pro_supported = fields.Nested(DateOrNoteSchema, required=True)
    legacy_supported = fields.Nested(DateOrNoteSchema, required=True)
    upgrade_path = fields.List(
        fields.String(), required=False, allow_none=True
    )
    compatible_ubuntu_lts = fields.List(
        fields.Nested(CompatibleLTSSchema),
        required=False,
        allow_none=True,
    )


class GetProductsQuerySchema(Schema):
    include_expired = fields.Boolean(load_default=False)


class SlugValidationMixin:
    @validates("slug")
    def validate_slug(self, value):
        if value is None:
            return
        stripped = value.strip()
        if stripped:
            _validate_slug_format(stripped)


class CreateDeploymentBodySchema(SlugValidationMixin, Schema):
    """Schema for deployment input in POST /products."""

    slug = fields.String(required=False, load_default=None)
    name = fields.String(required=True)
    artifact_type = fields.String(
        required=True, validate=OneOf(ARTIFACT_TYPES)
    )

    @post_load
    def normalize_slug(self, data, **kwargs):
        if "slug" in data and data["slug"] is not None:
            stripped = data["slug"].strip()
            data["slug"] = stripped if stripped else None
        return data


class CreateProductBodySchema(SlugValidationMixin, Schema):
    """Schema for POST /products request body."""

    slug = fields.String(required=False, load_default=None)
    name = fields.String(required=True)
    deployments = fields.List(
        fields.Nested(CreateDeploymentBodySchema),
        required=True,
        allow_none=False,
        validate=Length(min=1),
    )

    @post_load
    def normalize_fields(self, data, **kwargs):
        if "slug" in data and data["slug"] is not None:
            stripped = data["slug"].strip()
            data["slug"] = stripped if stripped else None
        if "name" in data:
            stripped_name = data["name"].strip()
            if not stripped_name:
                raise ValidationError(
                    "Name must not be blank.",
                    field_name="name",
                )
            data["name"] = stripped_name
        return data

    @validates_schema
    def validate_unique_deployment_slugs(self, data, **kwargs):
        deployments = data.get("deployments") or []
        slugs = [deployment.get("slug") for deployment in deployments]

        if len(slugs) != len(set(slugs)):
            raise ValidationError(
                "Deployment slugs must be unique within a product.",
                field_name="deployments",
            )


class ErrorSchema(Schema):
    """For errors with no field-level detail (e.g. 401, 403)."""

    message = fields.String(required=True)


class ErrorDetailSchema(Schema):
    """For errors with field-level context (400, 404, 409)."""

    message = fields.String(required=True)
    details = fields.Dict(required=True)
