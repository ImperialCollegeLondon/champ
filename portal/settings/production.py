"""This module contains those settings required for production
deployment as an Open OnDemand app that are not expected to vary
between deployments. This module is not intended to be used directly
but imported into another module where deployment specific settings
are given.
"""

import os
from pathlib import Path

from .settings import *  # noqa: F401, F403

DEBUG = False
SECRET_KEY = os.environ["SECRET_KEY"]
SECURE_BROWSER_XSS_FILTER = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = 15552000
USE_X_FORWARDED_HOST = True
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"


# The below settings are sensible defaults but may nonetheless need
# to be overridden for different sites
DATABASES["default"]["NAME"] = (  # noqa: F405
    Path(os.environ["HOME"]) / "chemistry_portal_db_DO_NOT_DELETE.sqlite3"
)

JOBS_DIR = Path(os.environ["HOME"]) / "portal_jobs"
