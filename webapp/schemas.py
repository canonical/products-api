from marshmallow import Schema, ValidationError, fields, validates_schema
from marshmallow.validate import OneOf, Length

from webapp.constants import ARTIFACT_TYPES, ARCHITECTURES


class DateOrNoteSchema(Schema):
    """DateOrNote support lifecycle field."""

    date = fields.Date(required=False, allow_none=True)
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

    slug = fields.String(dump_only=True)
    name = fields.String(required=True)
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
