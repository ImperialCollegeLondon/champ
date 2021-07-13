from urllib.parse import urljoin

from django.conf import settings


def app_name(request):
    return {"APP_NAME": settings.APP_NAME}


def app_version(request):
    return {"APP_VERSION": settings.VERSION}


def status_link(request):
    return {"STATUS_LINK": settings.PORTAL_CONFIG["status_link"]}


def active_jobs_link(request):
    scheme = "https://" if request.is_secure() else "http://"
    return {
        "ACTIVE_JOBS_LINK": urljoin(
            scheme + request.get_host(), "pun/sys/dashboard/activejobs"
        )
    }
