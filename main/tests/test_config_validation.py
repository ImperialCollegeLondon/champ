from pathlib import Path
from unittest import TestCase

import yaml
from marshmallow import ValidationError

from config_validation import (
    ConfigSchema,
    ExternalLinkSchema,
    FileSchema,
    FilesSchema,
    ResourceSchema,
    SoftwareSchema,
    TimeoutsSchema,
)
from main.software import clean_software_config

TEST_DATA_PATH = Path(__file__).absolute().parent / "test_data"


def without_key(d, key):
    """Return a copy of dict `d` with `key` removed."""
    d2 = d.copy()
    d2.pop(key)
    return d2


class SchemaTestCase(TestCase):
    def required_fields(self, fields):
        for field in fields:
            with self.assertRaises(ValidationError):
                self.schema.load(without_key(self.valid_data, field))

    def field_types(self, incorrect_types):
        for key, value in incorrect_types.items():
            with self.assertRaises(ValidationError):
                self.schema.load({**self.valid_data, key: value})


class TestResourceSchema(SchemaTestCase):
    valid_data = {"description": "", "script_lines": ""}
    schema = ResourceSchema()

    def test_fields_required(self):
        """All fields for required for successful validation"""
        self.required_fields(["description", "script_lines"])

    def test_fields_type(self):
        """Non-string values for fields do not pass validation"""
        self.field_types({"description": 0, "script_lines": 0})

    def test_valid(self):
        """Valid data should not trigger a validation error"""
        self.schema.load(self.valid_data)


class TestExternalLinkSchema(ExternalLinkSchema):
    valid_data = {"text": "", "url": "https://foo.com"}
    schema = ResourceSchema()

    def test_fields_required(self):
        """All fields for required for successful validation"""
        self.required_fields(["text", "url"])

    def test_fields_type(self):
        """Non-string values for fields do not pass validation"""
        self.field_types({"description": 0, "script_lines": 0})

    def test_url_validation(self):
        """Url field must be a valid URL"""
        self.field_types({"url": "notaurl"})

    def test_valid(self):
        """Valid data should not trigger a validation error"""
        self.schema.load(self.valid_data)


class TestFileSchema(SchemaTestCase):
    valid_data = {"description": "", "key": ""}
    schema = FileSchema()

    def test_fields_required(self):
        """All fields for required for successful validation"""
        self.required_fields(["description", "key"])

    def test_fields_type(self):
        """Non-string values for fields do not pass validation"""
        self.field_types({"description": 0, "key": 0})

    def test_valid(self):
        """Valid data should not trigger a validation error"""
        self.schema.load(self.valid_data)


class TestFilesSchema(SchemaTestCase):
    valid_data = {
        "required": [TestFileSchema.valid_data],
        "optional": [TestFileSchema.valid_data],
    }
    schema = FilesSchema()

    def test_fields_required(self):
        self.required_fields(["required", "optional"])

    def test_empty(self):
        self.schema.load({"required": None, "optional": None})

    def test_field_types(self):
        self.field_types({"required": "", "optional": ""})

    def test_valid(self):
        self.schema.load(self.valid_data)


class TestSoftwareSchema(SchemaTestCase):
    files_data = TestFilesSchema.valid_data
    valid_data = dict(name="", input_files=files_data, commands="", help_text="")
    schema = SoftwareSchema()

    def test_fields_required(self):
        self.required_fields(["name", "input_files", "commands", "help_text"])

    def test_field_types(self):
        self.field_types({"name": 0, "input_files": "", "commands": 0, "help_text": 0})

    def test_valid(self):
        self.schema.load(self.valid_data)


class TestTimeoutsSchema(SchemaTestCase):
    valid_data = {"submit": 1, "status": 1, "delete": 1}
    schema = TimeoutsSchema()

    def test_fields_type(self):
        """Non-integer values for fields do not pass validation"""
        self.field_types({"submit": "", "status": "", "delete": ""})

    def test_valid(self):
        """Valid data should not trigger a validation error"""
        self.schema.load(self.valid_data)


class TestConfigSchema(SchemaTestCase):
    software = dict(
        name="", input_files=TestFilesSchema.valid_data, commands="", help_text=""
    )
    schema = ConfigSchema()

    valid_data = dict(
        resources=[TestResourceSchema.valid_data],
        software=[TestSoftwareSchema.valid_data],
        script_template="",
        custom_config_line_regex="",
        enabled_repositories=[""],
        external_links=[TestExternalLinkSchema.valid_data],
        cluster="",
        timeouts=TestTimeoutsSchema.valid_data,
    )

    def test_fields_required(self):
        self.required_fields(
            [
                "resources",
                "software",
                "script_template",
                "custom_config_line_regex",
                "enabled_repositories",
                "cluster",
            ]
        )

    def test_empty(self):
        self.schema.load({**self.valid_data, "resources": None})
        self.schema.load({**self.valid_data, "software": None})
        self.schema.load({**self.valid_data, "enabled_repositories": None})

    def test_field_types(self):
        self.field_types(
            dict(
                resources=0,
                software=0,
                script_template=0,
                custom_config_line_regex=0,
                enabled_repositories=0,
                cluster=0,
                timeouts=0,
            )
        )

    def test_valid(self):
        self.schema.load(self.valid_data)

    def test_test_config(self):
        """The configuration provided for running tests must be valid"""
        with open(TEST_DATA_PATH / "test_config.yaml") as f:
            self.schema.load(yaml.safe_load(f))


class TestCleanSoftwareConfig(TestCase):
    def test_replace_none(self):
        """"""
        config = dict(
            name="",
            input_files=dict(required=None, optional=None),
            commands="",
            help_text="",
        )
        config = clean_software_config(config)
        self.assertEqual(config["input_files"]["required"], [])
        self.assertEqual(config["input_files"]["optional"], [])
