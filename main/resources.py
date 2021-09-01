from django.conf import settings

from .models.custom import CustomResource

RESOURCES = settings.PORTAL_CONFIG["resources"] or []
RESOURCE_CHOICES = list(enumerate(s["description"] for s in RESOURCES))


def get_resource_choices():
    choices = list(enumerate(s["description"] for s in RESOURCES))
    custom_resources = CustomResource.objects.all()
    choices += list(enumerate((r.label for r in custom_resources), len(choices)))
    return choices


def get_resource(index):
    custom_resources = CustomResource.objects.all()
    all_resources = RESOURCES + [
        {"description": r.label, "script_lines": r.script_lines}
        for r in custom_resources
    ]
    return all_resources[index]
