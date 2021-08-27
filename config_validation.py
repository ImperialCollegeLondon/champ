from marshmallow import Schema, fields


class ResourceSchema(Schema):
    description = fields.Str(required=True)
    script_lines = fields.Str(required=True)


class FilesSchema(Schema):
    required = fields.Dict(
        keys=fields.Str(), values=fields.Str(), allow_none=True, required=True
    )
    optional = fields.Dict(
        keys=fields.Str(), values=fields.Str(), allow_none=True, required=True
    )


class SoftwareSchema(Schema):
    name = fields.Str(required=True)
    input_files = fields.Nested(FilesSchema, required=True)
    commands = fields.Str(required=True)
    help_text = fields.Str(required=True)


class ConfigSchema(Schema):
    resources = fields.Nested(ResourceSchema, many=True, allow_none=True, required=True)
    software = fields.Nested(SoftwareSchema, many=True, allow_none=True, required=True)
    script_template = fields.Str(required=True)
    custom_config_line_regex = fields.Str(required=True)
    enabled_repositories = fields.List(fields.Str, required=True, allow_none=True)
    external_links = fields.Dict(keys=fields.Str(), values=fields.Str())
    cluster = fields.Str(required=True)


if __name__ == "__main__":
    import sys

    import yaml

    with open(sys.argv[1]) as f:
        PORTAL_CONFIG = yaml.safe_load(f)

    ConfigSchema().load(PORTAL_CONFIG)
