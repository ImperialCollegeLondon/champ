from pathlib import Path

from ..models import Job
from .scheduler_mock import SchedulerTestCase

TEST_DATA_PATH = Path(__file__).absolute().parent / "test_data"


class TestViews(SchedulerTestCase):
    def test_index(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_create_job_get(self):
        response = self.client.get("/create_job")
        self.assertEqual(response.status_code, 200)

        form = response.context["form"]
        self.assertIn("com", form.fields)

    def test_create_job_post(self):
        test_input = "test.com"
        with (TEST_DATA_PATH / test_input).open() as f:
            response = self.client.post("/create_job", {"com": f})

        self.assertEqual(len(Job.objects.all()), 1)
        job = Job.objects.get()

        files = list(job.work_dir.glob("*"))
        self.assertIn(job.work_dir / test_input, files)
        with (job.work_dir / "sub.pbs").open() as f:
            self.assertIn(test_input, f.read())

        self.assertRedirects(response, f"/success/{job.pk}/")
