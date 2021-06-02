from django.conf import settings

SOFTWARE = settings.PORTAL_CONFIG["software"]

SOFTWARE_CHOICES = list(enumerate(s["name"] for s in SOFTWARE))
