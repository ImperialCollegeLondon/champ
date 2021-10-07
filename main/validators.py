import re

from django.conf import settings
from django.core.exceptions import ValidationError

ORCID_REGEX = re.compile(r"^\d{4}-\d{4}-\d{4}-(\d{3}X|\d{4})$")


def validate_config_lines(lines):
    """Check each line of the provided config file using settings.CONFIG_LINE_REGEX.

    args:
      lines (str): The config lines to check
    """
    lines = lines.strip()
    for line in lines.split("\n"):
        if settings.CONFIG_LINE_REGEX.match(line) is None:
            raise ValidationError(f"Invalid line: '{line}'")


def validate_orcid_id(orcid_id):
    """Check a provided ORCiD id is valid.

    args:
      orcid_id (str): the ORCiD to check
    """
    if not ORCID_REGEX.match(orcid_id):
        raise ValidationError("Invalid ORCID iD")
