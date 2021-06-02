from django.conf import settings

RESOURCES = settings.PORTAL_CONFIG["resources"]
RESOURCE_CHOICES = list(enumerate(s["description"] for s in RESOURCES))
