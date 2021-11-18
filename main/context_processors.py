from django.conf import settings

from .portal_config import get_portal_settings


def app_name(request):
    return {"APP_NAME": settings.APP_NAME}


def app_version(request):
    return {"APP_VERSION": settings.VERSION}


def external_links(request):
    return {"EXTERNAL_LINKS": get_portal_settings().EXTERNAL_LINKS}
