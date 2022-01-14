import importlib
import pkgutil
import re

from ..portal_config import get_portal_settings
from . import plugins

REPOSITORIES = {}
LABEL_REGEX = re.compile("^[a-zA-Z0-9_-]*$")


class RepositoryError(Exception):
    pass


def register(klass):
    if not LABEL_REGEX.match(klass.label):
        raise ValueError(
            "Unable to register repository. Label must contain only letters, numbers, "
            "underscores and dashes."
        )
    REPOSITORIES[klass.label] = klass()
    return klass


def get_repository(label):
    return REPOSITORIES[label]


def get_repositories():
    portal_settings = get_portal_settings()
    return {
        label: repo
        for label, repo in REPOSITORIES.items()
        if label in portal_settings.ENABLED_REPOSITORIES
    }


# import plugins, no need to do anything with them as they should use
# the register function
for _, plugin, _ in pkgutil.iter_modules(plugins.__path__, plugins.__name__ + "."):
    importlib.import_module(plugin)
