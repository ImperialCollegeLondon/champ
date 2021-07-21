import importlib
import pkgutil
import re

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


def get_repository(label):
    return REPOSITORIES[label]


def get_repositories():
    return REPOSITORIES.copy()


# import plugins, no need to do anything with them as they should use
# the register function
for _, plugin, _ in pkgutil.iter_modules(plugins.__path__, plugins.__name__ + "."):
    importlib.import_module(plugin)
