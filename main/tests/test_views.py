import shutil
import zipfile
from datetime import timedelta
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from ..models import (
    ROUNDING_INTERVAL,
    CustomConfig,
    CustomResource,
    Job,
    Profile,
    Project,
    Publication,
    Token,
)
from ..resources import RESOURCES
from ..software import SOFTWARE
from . import create_dummy_job
from .repository_mock import MockRepository
from .scheduler_mock import (
    SCHEDULER_ERROR_MESSAGE,
    SchedulerTestCase,
    raise_scheduler_error,
)

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
        self.custom_lines = "CUSTOM_LINES"
        self.config = CustomConfig.objects.create(
            label="foo", script_lines=self.custom_lines
        )
        self.test_input = "test.com"

    def test_create_job_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        form = response.context["form"]
        self.assertIn("file1", form.fields)

    def test_create_job_post(self):
        with (TEST_DATA_PATH / self.test_input).open() as f:
            response = self.client.post(self.url, {"file1": f})

        self.assertEqual(len(Job.objects.all()), 1)
        job = Job.objects.get()

        self.assertEqual(job.resources, RESOURCES[self.resources_index]["description"])
        self.assertEqual(job.software, SOFTWARE[self.software_index]["name"])

        files = list(job.work_dir.glob("*"))
        self.assertIn(job.work_dir / self.test_input, files)
        with (job.work_dir / "sub.pbs").open() as f:
            self.assertIn(self.test_input, f.read())

        self.assertRedirects(response, f"/list_jobs/?success={job.pk}")

    def test_create_job_post_optional(self):
        test_fchk = "test.fchk"
        with (TEST_DATA_PATH / self.test_input).open() as f, (
            TEST_DATA_PATH / test_fchk
        ).open() as f2:
            response = self.client.post(
                self.url,
                {"file1": f, "file2": f2},
            )
        self.assertEqual(len(Job.objects.all()), 1)
        job = Job.objects.get()

        files = list(job.work_dir.glob("*"))
        self.assertIn(job.work_dir / self.test_input, files)
        self.assertIn(job.work_dir / test_fchk, files)
        with (job.work_dir / "sub.pbs").open() as f:
            contents = f.read()
            self.assertIn(self.test_input, contents)
            self.assertIn(test_fchk, contents)

        self.assertRedirects(response, f"/list_jobs/?success={job.pk}")

    @patch("main.scheduler.submit", raise_scheduler_error)
    def test_create_job_failure(self):
        """Failure during job submission is caught"""
        with (TEST_DATA_PATH / self.test_input).open() as f:
            response = self.client.post(self.url, {"file1": f})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["message"],
            "Job submission failed\n\n" + SCHEDULER_ERROR_MESSAGE,
        )
        self.assertEqual(len(Job.objects.all()), 0)

    def test_create_job_custom_config_get(self):
        response = self.client.get(self.url + f"{self.config.pk}/")
        self.assertEqual(response.status_code, 200)

    def test_create_job_custom_config_post(self):
        with (TEST_DATA_PATH / self.test_input).open() as f:
            response = self.client.post(self.url + f"{self.config.pk}/", {"file1": f})
        job = Job.objects.get()
        self.assertRedirects(response, f"/list_jobs/?success={job.pk}")

        with (job.work_dir / "sub.pbs").open() as f:
            contents = f.read()
        self.assertIn(self.custom_lines, contents)


class TestListViews(SchedulerTestCase):
    def test_list_jobs(self):
        seconds = 1000
        job = create_dummy_job()

        response = self.client.get("/list_jobs/")
        jobs = response.context["table"].data.data
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].status, "Queueing")
        self.assertEqual(jobs[0].walltime, "N/A")

        # simulate job running and creating WALLTIME file
        self.scheduler.job_starts(job.job_id)
        with open(job.work_dir / "WALLTIME", "w") as f:
            f.write(f"{seconds}")

        response = self.client.get("/list_jobs/")
        jobs = response.context["table"].data.data
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].status, "Running")
        self.assertEqual(jobs[0].walltime, timedelta(seconds=seconds))

        self.scheduler.job_finishes(job.job_id)

        response = self.client.get("/list_jobs/")
        jobs = response.context["table"].data.data
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].status, "Completed")
        self.assertEqual(
            jobs[0].walltime,
            round(timedelta(seconds=seconds) / ROUNDING_INTERVAL) * ROUNDING_INTERVAL,
        )


class TestDeleteViews(SchedulerTestCase):
    def test_delete(self):
        job = create_dummy_job()

        response = self.client.get(f"/delete/{job.pk}/")
        self.assertEqual(len(Job.objects.all()), 0)
        self.assertRedirects(response, "/")


class TestJobTypeViews(TestCase):
    def test_get(self):
        response = self.client.get("/job_type/")
        self.assertEqual(response.status_code, 200)

    def test_get_with_custom_resource(self):
        label = "foo"
        CustomResource.objects.create(label=label)
        response = self.client.get("/job_type/")
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        choices = form.fields["resources"].choices.choices_func()
        self.assertIn((1, label), choices)

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


class TestCustomConfigView(TestCase):
    label = "foo"
    lines = "#PBS -N name"

    def test_get(self):
        """Get with no pk loads successfully"""
        response = self.client.get("/custom_config/")
        self.assertEqual(response.status_code, 200)

    def test_get_existing(self):
        """Get with pk loads with initial data"""
        config = CustomConfig.objects.create(label=self.label, script_lines=self.lines)
        response = self.client.get(f"/custom_config/{config.pk}/")
        self.assertEqual(response.status_code, 200)
        initial_data = response.context["form"].initial
        self.assertEqual(initial_data["label"], self.label)
        self.assertEqual(initial_data["script_lines"], self.lines)

    def test_post(self):
        """Post without pk should create a new CustomConfig object"""
        response = self.client.post(
            "/custom_config/", {"label": self.label, "script_lines": self.lines}
        )
        self.assertRedirects(response, "/profile/")
        config = CustomConfig.objects.get()
        self.assertEqual(config.label, self.label)
        self.assertEqual(config.script_lines, self.lines)

    def test_post_existing(self):
        """Post with pk should update existing CustomConfig object"""
        new_label = "new_label"
        new_lines = "#PBS -N new_name"
        config = CustomConfig.objects.create(label=self.label, script_lines=self.lines)

        response = self.client.post(
            f"/custom_config/{config.pk}/",
            {"label": new_label, "script_lines": new_lines},
        )
        self.assertRedirects(response, "/profile/")
        config = CustomConfig.objects.get()
        self.assertEqual(config.label, new_label)
        self.assertEqual(config.script_lines, new_lines)

    def test_404(self):
        """Request with pk for non-existant object should cause 404"""
        response = self.client.get("/custom_config/1/")
        self.assertEqual(response.status_code, 404)


class TestProfileView(TestCase):
    form_data = dict(
        orcid_id="0000-0000-0000-0000",
        family_name="family_name",
        given_names="given_names",
        affiliation="affiliation",
    )

    def test_get(self):
        """Get request should return with 200 status"""
        response = self.client.get("/profile/")
        self.assertEqual(response.status_code, 200)

    def test_existing(self):
        """Data from existing Profile instance should be used as initial data"""
        Profile.objects.create(**self.form_data)
        response = self.client.get("/profile/")
        initial_data = response.context["form"].initial
        initial_data.pop("id")
        self.assertEqual(initial_data, self.form_data)

    def test_get_with_custom_config(self):
        """Existing CustomConfig's should be included in the response"""
        config = CustomConfig.objects.create(label="foo", script_lines="#PBS -N name")
        response = self.client.get("/profile/")
        self.assertEqual(response.status_code, 200)

        table = response.context["table"]
        self.assertEqual(table.data.data.get(), config)

    def test_post_create(self):
        response = self.client.post("/profile/", self.form_data)
        self.assertRedirects(response, "/")

        profile = Profile.objects.get()
        self.assertEqual(profile.orcid_id, self.form_data["orcid_id"])

    def test_post_update(self):
        orcid_id2 = "0000-0000-0000-000X"
        Profile.objects.create(orcid_id=orcid_id2)
        response = self.client.post("/profile/", self.form_data)
        self.assertRedirects(response, "/")

        profile = Profile.objects.get()
        self.assertEqual(profile.orcid_id, self.form_data["orcid_id"])


class TestProfileDelete(SchedulerTestCase):
    def test_existing(self):
        """Existing profile should be deleted"""
        Profile.objects.create()
        self.assertEqual(Profile.objects.count(), 1)
        response = self.client.get("/delete_profile/")
        self.assertRedirects(response, "/")
        self.assertEqual(Profile.objects.count(), 0)

    def test_no_existing(self):
        """Calling with no existing profile should not cause error"""
        self.assertEqual(Profile.objects.count(), 0)
        response = self.client.get("/delete_profile/")
        self.assertRedirects(response, "/")
        self.assertEqual(Profile.objects.count(), 0)


class TestDownloadView(SchedulerTestCase):
    def setUp(self):
        super().setUp()
        self.test_input = "test.com"
        project = Project.objects.create(name="test")

        with (TEST_DATA_PATH / self.test_input).open("rb") as f:
            self.job = Job.objects.create_job("", {"file1": f}, project, 0, 0)

    def test_archive(self):
        """Downloaded zip archive should contain files in job.work_dir"""
        self.job.status = "Completed"
        self.job.save()

        response = self.client.get(f"/download/{self.job.pk}/")
        streamed_bytes = BytesIO(b"".join(response.streaming_content))
        zf = zipfile.ZipFile(streamed_bytes)
        dir_name = self.job.work_dir.name
        self.assertEqual(
            sorted(zf.namelist()), [f"{dir_name}/sub.pbs", f"{dir_name}/test.com"]
        )
        with zf.open(dir_name + "/" + self.test_input) as f:
            with (TEST_DATA_PATH / self.test_input).open("rb") as f2:
                self.assertEqual(f.read(), f2.read())

    def test_not_complete(self):
        """Uncompleted jobs should not be downloadable"""
        response = self.client.get(f"/download/{self.job.pk}/")
        self.assertEqual(response.status_code, 404)

    def test_invalid_job(self):
        """Trying to download unknown job should give 404"""
        response = self.client.get(f"/download/{self.job.pk + 1}/")
        self.assertEqual(response.status_code, 404)


class TestPublishView(SchedulerTestCase):
    def setUp(self):
        self.profile = Profile.objects.create(
            orcid_id="0000-0000-0000-0000",
            given_names="given names",
            family_name="family name",
            affiliation="affiliation",
        )
        super().setUp()

    def test_no_profile(self):
        """Profile information must be available for publications to be made"""
        self.profile.delete()
        job = create_dummy_job(description="")
        response = self.client.get(f"/publish/{job.pk}/")
        self.assertIn("Profile information not set.", response.context["message"])

    def test_incomplete_profile(self):
        """Profile information must be fully complete for publications to be made.
        This test covers a transition case caused by changes to the Profile model.
        """
        self.profile.family_name = ""
        self.profile.save()
        job = create_dummy_job(description="")
        response = self.client.get(f"/publish/{job.pk}/")
        self.assertIn("Profile information not set.", response.context["message"])

    def test_unknown_job(self):
        """Trying to publish non-existant job gives 404"""
        response = self.client.get("/publish/1/")
        self.assertEqual(response.status_code, 404)

    def test_already_published(self):
        """Should not be able to publish an already published job"""
        job = create_dummy_job()
        Publication.objects.create(
            job=job, repo_label="label", repo_name="name", doi="doi"
        )
        response = self.client.get(f"/publish/{job.pk}/")
        self.assertEqual(response.context["message"], "Job already published")
        self.assertEqual(Publication.objects.count(), 1)

    def test_no_description(self):
        """Trying to publish a job without a description gives a clean error message"""
        job = create_dummy_job(description="")
        Token.objects.create(label="test", value="test")
        response = self.client.get(f"/publish/{job.pk}/")
        self.assertEqual(
            response.context["message"], "Job must have a description to be published"
        )

    def test_no_files_to_publish(self):
        """Trying to publish a job with FILES_TO_PUBLISH file fails"""
        job = create_dummy_job()
        Token.objects.create(label="mock", value="test")
        response = self.client.get(f"/publish/{job.pk}/")
        self.assertIn(
            "Unable to open 'FILES_TO_PUBLISH' in job directory",
            response.context["message"],
        )

    @patch("main.views.get_repositories", lambda: {"mock": MockRepository()})
    def test_working(self):
        """For a valid job publishing should create a Publication record"""
        job = create_dummy_job(description="description")
        (job.work_dir / "FILES_TO_PUBLISH").touch()
        (job.work_dir / "METADATA").touch()
        Token.objects.create(label="mock", value="test")
        response = self.client.get(f"/publish/{job.pk}/")
        self.assertRedirects(response, f"/job/{job.pk}/")
        self.assertEqual(Publication.objects.count(), 1)


class TestDirectoryView(SchedulerTestCase):
    def test_working(self):
        """All files in job directory should be presented in table"""
        job = create_dummy_job()
        (job.work_dir / "file1").touch()

        response = self.client.get(f"/directory/{job.pk}/")
        files = response.context["table"].data.data
        self.assertEqual(files[0]["name"], "file1")
        self.assertEqual(files[1]["name"], "sub.pbs")

    def test_missing_directory(self):
        """Appropriate message is displayed if job directory cannot be found"""
        job = create_dummy_job()
        shutil.rmtree(job.work_dir)
        response = self.client.get(f"/directory/{job.pk}/")
        self.assertIn("Job directory not found", response.context["message"])


class TestProfilePublishInteraction(SchedulerTestCase):
    def test(self):
        """Regression test for bug where accessing the profile would allow job
        publication without profile information being set."""
        response = self.client.get("/profile/")
        self.assertEqual(response.status_code, 200)

        job = create_dummy_job()
        Token.objects.create(label="mock", value="test")
        response = self.client.get(f"/publish/{job.pk}/")

        self.assertIn("Profile information not set", response.context["message"])
