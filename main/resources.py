from django.conf import settings

RESOURCES = settings.RESOURCES
RESOURCE_CHOICES = list(enumerate(s["description"] for s in settings.RESOURCES))
