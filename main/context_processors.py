from django.conf import settings


def app_name(request):
    return {"APP_NAME": settings.APP_NAME}


def site(request):
    return {"SITE_URL": settings.SITE_URL}
