from django.conf import settings


def app_name(request):
    return {"APP_NAME": settings.APP_NAME}


def app_version(request):
    return {"APP_VERSION": settings.VERSION}


def status_link(request):
    return {"STATUS_LINK": settings.PORTAL_CONFIG["status_link"]}
