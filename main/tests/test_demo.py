import os
import shutil
from pathlib import Path
from unittest import skipIf
from unittest.mock import patch

from django.test import TestCase

from main import scheduler
from main.models import Job, Project
from main.portal_config import SettingsGetter

TEST_DATA_PATH = Path(__file__).absolute().parent.parent.parent / "demo_cluster"


@skipIf(
    os.getenv("DEMO_CLUSTER") is None,
    "DEMO_CLUSTER environment variable not set",
)
@patch(
    "main.portal_config.get_portal_settings._settings",
    SettingsGetter(TEST_DATA_PATH / "demo_portal_config.yaml")(),
)
class DemoTest(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="foo")

    def tearDown(self):
        shutil.rmtree("/tmp/00000001", ignore_errors=True)

    def test_submission(self):
        Job.objects.create_job("", {}, self.project, 0, 0)
        Job.objects.get()

    def test_status(self):
        job = Job.objects.create_job("", {}, self.project, 0, 0)

        status = scheduler.status(job.job_id)
        self.assertIn(status, ("queued", "running"))

    def test_delete(self):
        job = Job.objects.create_job("", {}, self.project, 0, 0)

        scheduler.delete(job.job_id)

        status = scheduler.status(job.job_id)
        self.assertEqual(status, "completed")
