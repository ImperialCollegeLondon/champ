from django.db import models

from ..validators import validate_config_lines


class Custom(models.Model):
    """An abstract class for custom content to be added to job script templates."""

    class Meta:
        abstract = True

    label = models.CharField(max_length=50)
    script_lines = models.TextField(max_length=1000, validators=[validate_config_lines])

    def __str__(self):
        return f"{self.label}"


class CustomConfig(Custom):
    """Custom scheduler directives not related to job resources."""

    pass


class CustomResource(Custom):
    """Custom scheduler directives related to job resources."""

    pass
