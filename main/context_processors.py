from django.conf import settings


def app_name(request):
    return {"APP_NAME": settings.APP_NAME}


def app_version(request):
    return {"APP_VERSION": settings.VERSION}
