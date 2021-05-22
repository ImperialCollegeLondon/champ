import os
import sys

# swap Python interpreter to provided venv
INTERP = os.environ["PORTAL_VENV"]
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

import django  # noqa: E402
from django.core import management  # noqa: E402

import portal.wsgi  # noqa: E402

# apply any new migrations to user's db
django.setup()
management.call_command("migrate", no_input=True)

application = portal.wsgi.application
