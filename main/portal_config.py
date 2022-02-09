import re
from types import SimpleNamespace

import yaml
from django.conf import settings

from config_validation import ConfigSchema


class SettingsGetter:
    """"""

    _settings = None

    def __init__(self, filepath):
        self.filepath = filepath

    def __call__(self):
        if not self._settings:
            with open(self.filepath) as f:
                portal_config = yaml.safe_load(f)
            ConfigSchema().load(portal_config)

            attrs = dict(
                CONFIG_LINE_REGEX=re.compile(portal_config["custom_config_line_regex"]),
                ENABLED_REPOSITORIES=portal_config.get("enabled_repositories") or [],
                CLUSTER=portal_config["cluster"],
                CONFIG_LINK=portal_config.get("config_link"),
                SOFTWARE=portal_config.get("software"),
                RESOURCES=portal_config.get("resources"),
                SCRIPT_TEMPLATE=portal_config.get("script_template"),
                EXTERNAL_LINKS=portal_config.get("external_links") or [],
            )
            self._settings = SimpleNamespace(**attrs)
        return self._settings


get_portal_settings = SettingsGetter(settings.PORTAL_CONFIG_PATH)
