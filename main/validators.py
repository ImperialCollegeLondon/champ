from django.conf import settings
from django.core.exceptions import ValidationError


def validate_config_lines(lines):
    lines = lines.strip()
    for line in lines.split("\n"):
        if settings.CONFIG_LINE_REGEX.match(line) is None:
            raise ValidationError(f"Invalid line: '{line}'")
