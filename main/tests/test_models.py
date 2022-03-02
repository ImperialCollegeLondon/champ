from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

from django.core.exceptions import ValidationError

from ..models import ROUNDING_INTERVAL, CustomConfig, Job, Profile, Project
from ..portal_config import SettingsGetter
from ..scheduler import SchedulerError
from . import create_dummy_job
from .scheduler_mock import SchedulerTestCase, raise_scheduler_error

TEST_DATA_PATH = Path(__file__).absolute().parent / "test_data"


@patch(
    "main.portal_config.get_portal_settings._settings",
    SettingsGetter(TEST_DATA_PATH / "test_config.yaml")(),
)
class Test(SchedulerTestCase):
    def setUp(self):
        super().setUp()
        self.project = Project.objects.create(name="test")

    def test_project_deletion(self):
        """Job remains with null value after associated project is deleted"""

        job = create_dummy_job(project=self.project)

        self.assertEqual(job.project, self.project)
        self.project.delete()

        self.assertEqual(len(Job.objects.all()), 1)
        job.refresh_from_db()
        self.assertEqual(job.project, None)

    @patch("main.scheduler.submit", raise_scheduler_error)
    def test_failed_job_creation(self):
        """Test that no mess is left if job creation fails"""
        with self.assertRaises(SchedulerError):
            create_dummy_job(project=self.project)
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

    def test_walltime_queueing(self):
        """Queueing jobs always give walltime as 'N/A'"""
        seconds = 6000
        job = Job.objects.create(
            status=Job.QUEUEING,
            resources="",
            software="",
        )

        self.assertEqual(job.walltime, "N/A")

        job.work_dir.mkdir()
        with open(job.work_dir / "WALLTIME", "w") as f:
            f.write(f"{seconds}")

        self.assertEqual(job.walltime, "N/A")

    def test_walltime_running(self):
        """Running jobs return walltime from file"""
        seconds = 6000
        job = Job.objects.create(
            status=Job.RUNNING,
            resources="",
            software="",
        )

        self.assertEqual(job.walltime, "Unknown")

        job.work_dir.mkdir()
        with open(job.work_dir / "WALLTIME", "w") as f:
            f.write(f"{seconds}")

        self.assertEqual(job.walltime, timedelta(seconds=seconds))
        self.assertIs(job._walltime, None)

    def test_walltime_completed(self):
        """Completed jobs return walltime from model field else 'Unknown'"""
        seconds = 6000
        job = Job.objects.create(
            status=Job.COMPLETED,
            resources="",
            software="",
        )
        self.assertEqual(job.walltime, "Unknown")

        # even if a WALLTIME file is on disk it won't be read
        job.work_dir.mkdir()
        with open(job.work_dir / "WALLTIME", "w") as f:
            f.write(f"{seconds}")

        self.assertEqual(job.walltime, "Unknown")

        job._walltime = timedelta(seconds=seconds)
        job.save()
        self.assertEqual(job.walltime, timedelta(seconds=seconds))

    def test_walltime_assignment(self):
        """Value assigned to walltime is rounded according to ROUNDING_INTERVAL"""
        job = Job.objects.create(
            status=Job.COMPLETED,
            resources="",
            software="",
        )

        job.walltime = ROUNDING_INTERVAL
        self.assertEqual(job.walltime, ROUNDING_INTERVAL)

        job.walltime = ROUNDING_INTERVAL + timedelta(seconds=1)
        self.assertEqual(job.walltime, ROUNDING_INTERVAL)

        job.walltime = ROUNDING_INTERVAL - timedelta(seconds=1)
        self.assertEqual(job.walltime, ROUNDING_INTERVAL)

        job.walltime = 1.55 * ROUNDING_INTERVAL
        self.assertEqual(job.walltime, 2 * ROUNDING_INTERVAL)

    def test_profile_orcid_id(self):
        """Validation should catch incorrectly formatted ids"""
        self.clean_profile("0000-0000-0000-0000")
        self.clean_profile("0000-0000-0000-000X")

        # incorrect character at end
        with self.assertRaises(ValidationError):
            self.clean_profile(orcid_id="0000-0000-0000-000A")

        # too short
        with self.assertRaises(ValidationError):
            self.clean_profile(orcid_id="0000-0000-0000-000")

        # too long
        with self.assertRaises(ValidationError):
            self.clean_profile(orcid_id="0000-0000-0000-00000")

        # letter not at end
        with self.assertRaises(ValidationError):
            self.clean_profile(orcid_id="0000-000X-0000-00000")

    def clean_profile(self, orcid_id):
        other_data = dict(
            family_name="family_name",
            given_names="given_names",
            affiliation="affiliation",
        )
        Profile(orcid_id=orcid_id, **other_data).full_clean()

    def delete_job_without_job_id(self):
        """Job records with a job_id can be deleted without error"""
        job = create_dummy_job()
        job.job_id = ""
        job.save()
        job.delete()
