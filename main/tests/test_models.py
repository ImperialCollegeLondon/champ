from pathlib import Path
from unittest.mock import patch

from django.core.exceptions import ValidationError

from ..models import CustomConfig, Job, Project
from ..scheduler import SchedulerError
from . import create_dummy_job
from .scheduler_mock import SchedulerTestCase, raise_scheduler_error


class Test(SchedulerTestCase):
    def setUp(self):
        super().setUp()
        self.project = Project.objects.create(name="test")

    def test_project_deletion(self):
        """Job remains with null value after associated project is deleted"""

        job = create_dummy_job(self.project)

        self.assertEqual(job.project, self.project)
        self.project.delete()

        self.assertEqual(len(Job.objects.all()), 1)
        job.refresh_from_db()
        self.assertEqual(job.project, None)

    @patch("main.scheduler.submit", raise_scheduler_error)
    def test_failed_job_creation(self):
        """Test that no mess is left if job creation fails"""
        with self.assertRaises(SchedulerError):
            create_dummy_job(self.project)
        self.assertEqual(len(Job.objects.all()), 0)
        # work directory should be tidied up
        self.assertEqual(len(list(Path(self.tmp_dir.name).glob("*"))), 0)

    def test_custom_config_validation(self):
        with self.assertRaises(ValidationError):
            CustomConfig(label="test", script_lines="").full_clean()
        with self.assertRaises(ValidationError):
            CustomConfig(label="test", script_lines="#PBS").full_clean()
        CustomConfig(label="test", script_lines="#PBS -N job_name").full_clean()
        CustomConfig(
            label="test", script_lines="#PBS -N job_name\n#PBS -N job_name"
        ).full_clean()
        with self.assertRaises(ValidationError):
            CustomConfig(
                label="test", script_lines="#PBS -N job_name\n\n#PBS -N job_name"
            ).full_clean()
        CustomConfig(label="test", script_lines="#PBS -N job_name\n\n").full_clean()
