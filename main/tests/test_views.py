from ..models import Job
from .scheduler_mock import SchedulerTestCase


class TestViews(SchedulerTestCase):
    def test_index(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_create_job_get(self):
        response = self.client.get("/create_job")
        self.assertEqual(response.status_code, 200)

    def test_create_job_post(self):
        response = self.client.post("/create_job", {})
        self.assertEqual(len(Job.objects.all()), 1)
        job = Job.objects.get()
        self.assertRedirects(response, f"/success/{job.pk}/")
