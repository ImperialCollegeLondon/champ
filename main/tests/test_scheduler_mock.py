from .scheduler_mock import SchedulerTestCase


class TestJobSubmission(SchedulerTestCase):
    """A series of tests for the mock scheduler interface to check it
    reproduces the behaviour of the live scheduler"""

    def test_submit(self):
        from main.scheduler import submit

        submit("", "")
        self.assertEqual(self.scheduler.queued_jobs, {"00000001.pbs"})

        submit("", "")
        self.assertEqual(self.scheduler.queued_jobs, {"00000001.pbs", "00000002.pbs"})

    def test_status(self):
        from main.scheduler import status, submit

        job_id = submit("", "")
        self.assertEqual(status(job_id), "queueing")

        self.scheduler.job_starts(job_id)
        self.assertEqual(status(job_id), "running")

        self.scheduler.job_finishes(job_id)
        self.assertEqual(status(job_id), "completed")

    def test_delete(self):
        from main.scheduler import delete, status, submit

        job_id = submit("", "")
        delete(job_id)
        self.assertEqual(status(job_id), "completed")

        job_id = submit("", "")
        self.scheduler.job_starts(job_id)
        delete(job_id)
        self.assertEqual(status(job_id), "completed")

        job_id = submit("", "")
        self.scheduler.job_starts(job_id)
        self.scheduler.job_finishes(job_id)
        delete(job_id)
