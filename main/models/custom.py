from django.db import models

from ..validators import validate_config_lines


class Custom(models.Model):
    class Meta:
        abstract = True

    label = models.CharField(max_length=50)
    script_lines = models.TextField(max_length=1000, validators=[validate_config_lines])

    def __str__(self):
        return f"{self.label}"


class CustomConfig(Custom):
    pass


class CustomResource(Custom):
    pass
