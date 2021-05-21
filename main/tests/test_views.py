from pathlib import Path

from ..models import Job
from .scheduler_mock import SchedulerTestCase

TEST_DATA_PATH = Path(__file__).absolute().parent / "test_data"


class TestViews(SchedulerTestCase):
    def test_index(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_create_job_get(self):
        response = self.client.get("/create_job/")
        self.assertEqual(response.status_code, 200)

        form = response.context["form"]
        self.assertIn("com", form.fields)

    def test_create_job_post(self):
        test_input = "test.com"
        with (TEST_DATA_PATH / test_input).open() as f:
            response = self.client.post("/create_job/", {"com": f})

        self.assertEqual(len(Job.objects.all()), 1)
        job = Job.objects.get()

        files = list(job.work_dir.glob("*"))
        self.assertIn(job.work_dir / test_input, files)
        with (job.work_dir / "sub.pbs").open() as f:
            self.assertIn(test_input, f.read())

        self.assertRedirects(response, f"/success/{job.pk}/")

    def test_create_job_post_optional(self):
        test_input = "test.com"
        test_fchk = "test.fchk"
        with (TEST_DATA_PATH / test_input).open() as f, (
            TEST_DATA_PATH / test_fchk
        ).open() as f2:
            response = self.client.post("/create_job/", {"com": f, "fchk": f2})

        self.assertEqual(len(Job.objects.all()), 1)
        job = Job.objects.get()

        files = list(job.work_dir.glob("*"))
        self.assertIn(job.work_dir / test_input, files)
        self.assertIn(job.work_dir / test_fchk, files)
        with (job.work_dir / "sub.pbs").open() as f:
            contents = f.read()
            self.assertIn(test_input, contents)
            self.assertIn(test_fchk, contents)

        self.assertRedirects(response, f"/success/{job.pk}/")

    def test_list_jobs(self):
        job = Job.objects.create_job({})

        response = self.client.get("/list_jobs/")
        jobs = response.context["jobs"]
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].status, "Queueing")

        self.scheduler.job_starts(job.job_id)

        response = self.client.get("/list_jobs/")
        jobs = response.context["jobs"]
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].status, "Running")

        self.scheduler.job_finishes(job.job_id)

        response = self.client.get("/list_jobs/")
        jobs = response.context["jobs"]
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].status, "Completed")
