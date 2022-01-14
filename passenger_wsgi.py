import os
import sys

# swap Python interpreter to provided venv
INTERP = os.environ["PORTAL_VENV"]
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

sqlite_library_path = os.getenv("SQLITE_LIBRARY_PATH")
if sqlite_library_path:
    ld_library_path = os.environ["LD_LIBRARY_PATH"]
    if ld_library_path:
        ld_library_path = ":".join((ld_library_path, sqlite_library_path))
    else:
        ld_library_path = sqlite_library_path
    os.environ["LD_LIBRARY_PATH"] = ld_library_path

import django  # noqa: E402
from django.core import management  # noqa: E402

import portal.wsgi  # noqa: E402

# apply any new migrations to user's db
django.setup()
management.call_command("migrate", no_input=True)

application = portal.wsgi.application
