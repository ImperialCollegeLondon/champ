#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "portal.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    # if we are running tests ensure that the correct config file is used
    if sys.argv[1] == "test":
        os.environ["PORTAL_CONFIG_PATH"] = str(
            Path(__file__).absolute().parent
            / "main"
            / "tests"
            / "test_data"
            / "test_config.yaml"
        )
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
