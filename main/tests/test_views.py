from pathlib import Path
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from ..models import Job, Project
from ..resources import RESOURCES
from ..software import SOFTWARE
from . import create_dummy_job
from .scheduler_mock import SchedulerTestCase, raise_scheduler_error

TEST_DATA_PATH = Path(__file__).absolute().parent / "test_data"


class TestIndexViews(TestCase):
    def test_index(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)


class TestCreateJobViews(SchedulerTestCase):
    def setUp(self):
        super().setUp()
        self.project = Project.objects.create(name="test")
        self.resources_index = 0
        self.software_index = 0
        self.url = f"/create_job/{self.project.pk}/{self.resources_index}/{self.software_index}/"  # noqa: E501

    def test_create_job_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        form = response.context["form"]
        self.assertIn("file1", form.fields)

    def test_create_job_post(self):
        test_input = "test.com"
        with (TEST_DATA_PATH / test_input).open() as f:
            response = self.client.post(self.url, {"file1": f})

        self.assertEqual(len(Job.objects.all()), 1)
        job = Job.objects.get()

        self.assertEqual(job.resources, RESOURCES[self.resources_index]["description"])
        self.assertEqual(job.software, SOFTWARE[self.software_index]["name"])

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
            response = self.client.post(
                self.url,
                {"file1": f, "file2": f2},
            )

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

    @patch("main.scheduler.submit", raise_scheduler_error)
    def test_create_job_failure(self):
        """Failure during job submission is caught"""
        test_input = "test.com"
        with (TEST_DATA_PATH / test_input).open() as f:
            response = self.client.post(self.url, {"file1": f})
        self.assertRedirects(response, "/failed/")
        self.assertEqual(len(Job.objects.all()), 0)


class TestListViews(SchedulerTestCase):
    def test_list_jobs(self):
        project = Project.objects.create(name="test")
        job = create_dummy_job(project)

        response = self.client.get("/list_jobs/")
        jobs = response.context["table"].data.data
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].status, "Queueing")

        self.scheduler.job_starts(job.job_id)

        response = self.client.get("/list_jobs/")
        jobs = response.context["table"].data.data
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].status, "Running")

        self.scheduler.job_finishes(job.job_id)

        response = self.client.get("/list_jobs/")
        jobs = response.context["table"].data.data
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].status, "Completed")


class TestDeleteViews(SchedulerTestCase):
    def test_delete(self):
        project = Project.objects.create(name="test")
        job = create_dummy_job(project)

        response = self.client.get(f"/delete/{job.pk}/")
        self.assertEqual(len(Job.objects.all()), 0)
        self.assertRedirects(response, "/")


class TestJobTypeViews(TestCase):
    def test_get(self):
        response = self.client.get("/job_type/")
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        resources_index = 0
        software_index = 0
        project = Project.objects.create(name="test")
        response = self.client.post(
            "/job_type/",
            {
                "project": project.pk,
                "resources": resources_index,
                "software": software_index,
            },
        )
        self.assertRedirects(
            response, f"/create_job/{project.pk}/{resources_index}/{software_index}/"
        )


class TestProjectViews(TestCase):
    def test_get(self):
        response = self.client.get("/projects/")
        self.assertEqual(response.status_code, 200)

    def test_get_with_project(self):
        Project.objects.create(name="test")
        response = self.client.get("/projects/")
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post("/projects/", {"name": "test"})
        self.assertRedirects(response, "/")

        self.assertEqual(len(Project.objects.all()), 1)

    def test_delete(self):
        project = Project.objects.create(name="test")
        response = self.client.get(f"/delete_project/{project.pk}/")
        self.assertRedirects(response, "/")
        self.assertEqual(len(Project.objects.all()), 0)


class TestJobView(TestCase):
    def setUp(self):
        self.job = Job.objects.create(status="Q")
        self.url = reverse("main:job", args=[self.job.pk])

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        """Existing job object is updated, new job not created"""
        desc = "new_description"
        response = self.client.post(self.url, {"description": desc})
        self.assertRedirects(response, "/")
        job = Job.objects.get()
        self.assertEqual(job.description, desc)


class TestHelpView(TestCase):
    def test_get(self):
        response = self.client.get("/software_help/0/")
        self.assertEqual(response.status_code, 200)
