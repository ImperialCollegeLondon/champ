from django.conf import settings

from .models.custom import CustomResource

RESOURCES = settings.PORTAL_CONFIG["resources"] or []
RESOURCE_CHOICES = list(enumerate(s["description"] for s in RESOURCES))


def get_resource_choices():
    """Return the available choices for the user when selecting the resources for a
    job. This is a combination of options configured in the portal config file and any
    CustomResource objects. Data is returned in the format expected by the choices
    argument of django.forms.ChoiceField.

    returns:
      (list): the resource choices as a list of 2-ples.
    """
    choices = list(enumerate(s["description"] for s in RESOURCES))
    custom_resources = CustomResource.objects.all()
    choices += list(enumerate((r.label for r in custom_resources), len(choices)))
    return choices


def get_resource(index):
    """Return the resource configuration specificied by `index`. The possible resource
    configs are indexed from the concatenation of those from the protal config file
    followed by any CustomResource objects.

    args:
      index (int): index value of the resource configuration

    returns:
      (dict): the resource configuration
    """
    custom_resources = CustomResource.objects.all()
    all_resources = RESOURCES + [
        {"description": r.label, "script_lines": r.script_lines}
        for r in custom_resources
    ]
    return all_resources[index]
