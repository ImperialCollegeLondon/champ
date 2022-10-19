from pathlib import Path
from unittest import TestCase

import yaml

from ..portal_config import SettingsGetter

TEST_DATA_PATH = Path(__file__).absolute().parent / "test_data"


class TestSettingsGetter(TestCase):
    def test_timeout_defaults(self):
        config_path = TEST_DATA_PATH / "timeouts_test_config.yaml"
        getter = SettingsGetter(config_path)
        settings = getter()
        timeouts = settings.TIMEOUTS
        defaults = SettingsGetter.defaults["timeouts"]

        with open(config_path) as f:
            raw_settings = yaml.safe_load(f)
        self.assertEqual(timeouts["submit"], defaults["submit"])
        self.assertEqual(timeouts["status"], raw_settings["timeouts"]["status"])
        self.assertEqual(timeouts["delete"], defaults["delete"])
