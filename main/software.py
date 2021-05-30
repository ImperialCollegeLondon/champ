from django.conf import settings

SOFTWARE = settings.SOFTWARE

SOFTWARE_CHOICES = list(enumerate(s["name"] for s in settings.SOFTWARE))
