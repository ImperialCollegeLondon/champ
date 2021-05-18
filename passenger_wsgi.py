import os
import sys

# swap Python interpreter to provided venv
INTERP = os.environ["PORTAL_VENV"]
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

import portal.wsgi  # noqa: E402

application = portal.wsgi.application
