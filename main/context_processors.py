from django.conf import settings


def app_name(request):
    return {"APP_NAME": settings.APP_NAME}


def app_version(request):
    return {"APP_VERSION": settings.VERSION}


def external_links(request):
    return {"EXTERNAL_LINKS": settings.PORTAL_CONFIG.get("external_links", [])}


def index_page_templates(request):
    return {"INDEX_PAGE_TEMPLATES": ["main/welcome_override.html", "main/welcome.html"]}


def menu_style_templates(request):
    return {
        "MENU_STYLE_TEMPLATES": [
            "main/menu_style_override.html",
            "main/menu_style.html",
        ]
    }
