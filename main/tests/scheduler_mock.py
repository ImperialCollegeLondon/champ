import tempfile
from pathlib import Path
from unittest.mock import patch

from django.test import TestCase

from ..scheduler import SchedulerError


class Scheduler:
    """A testing replacement for `scheduler.py` that mocks an interface to
    a live cluster scheduler."""

    def __init__(self):
        self.queued_jobs = set()
        self.running_jobs = set()
        self.completed_jobs = set()
        self.current_id = 1

    def submit(self, script_path, submission_dir):
        job_id = f"{self.current_id:08d}.pbs"
        self.current_id += 1
        self.queued_jobs.add(job_id)
        return job_id

    def status(self, job_id):
        if job_id in self.queued_jobs:
            return "queueing"
        elif job_id in self.running_jobs:
            return "running"
        else:
            return "completed"

    def delete(self, job_id):
        if job_id not in self.queued_jobs and job_id not in self.running_jobs:
            return
        self.completed_jobs.add(job_id)
        self.queued_jobs.discard(job_id)
        self.running_jobs.discard(job_id)

    def job_starts(self, job_id):
        """Simulate a job starting execution"""
        self.queued_jobs.remove(job_id)
        self.running_jobs.add(job_id)

    def job_finishes(self, job_id):
        """Simulate a job finishing execution"""
        self.running_jobs.remove(job_id)
        self.completed_jobs.add(job_id)


class SchedulerTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.scheduler = Scheduler()
        self.submit_patcher = patch("main.scheduler.submit", self.scheduler.submit)
        self.submit_patcher.start()
        self.status_patcher = patch("main.scheduler.status", self.scheduler.status)
        self.status_patcher.start()
        self.delete_patcher = patch("main.scheduler.delete", self.scheduler.delete)
        self.delete_patcher.start()

        self.tmp_dir = tempfile.TemporaryDirectory()
        self.work_dir_patcher = patch(
            "main.models.settings.JOBS_DIR", Path(self.tmp_dir.name)
        )
        self.work_dir_patcher.start()

    def tearDown(self):
        super().tearDown()
        self.submit_patcher.stop()
        self.status_patcher.stop()
        self.delete_patcher.stop()

        self.tmp_dir.cleanup()
        self.work_dir_patcher.stop()


def raise_scheduler_error(job_id, work_dir):
    """Raises a scheduler.SchedulerError to simulate failure of job
    submision.
    """
    raise SchedulerError()
