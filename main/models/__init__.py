import shutil
import time
from datetime import timedelta
from itertools import chain
from pathlib import Path

from django.conf import settings
from django.db import models
from django.urls import reverse

from .. import scheduler
from ..resources import get_resource
from ..software import SOFTWARE
from ..validators import validate_orcid_id
from .custom import CustomConfig, CustomResource  # noqa: F401

ROUNDING_INTERVAL = timedelta(seconds=15)


class JobManager(models.Manager):
    """A custom model Manager for the Job class"""

    def create_job(
        self,
        description,
        input_files,
        project,
        resource_index,
        software_index,
        custom_config=None,
    ):
        """Create a new Job object, create the working directory, save the provided
        input files, produce the submission script and submit it.

        Args:
          description (str): Saved as the description field of the new job object
          input_files (dict[str, BinaryIO]): A mapping between job template insertion
            points (keys) and uploaded files (values)
          project (Project): Saved as the project field of the new job object
          resource_index (int): index of the resource configuration for this job
          software_index (int): index of the software configuration for this job
          custom_config (CustomConfig): custom scheduler directives to be added to the
            job template
        Returns:
          Job: The newly created Job object

        """
        resources = get_resource(resource_index)
        software = SOFTWARE[software_index]
        job = self.create(
            status="Queueing",
            description=description,
            project=project,
            resources=resources["description"],
            software=software["name"],
        )

        job.work_dir.mkdir(parents=True)
        for inp in input_files.values():
            with (job.work_dir / Path(inp.name).name).open("wb") as f:
                f.write(inp.read())

        script_path = job.work_dir / "sub.sh"

        files_spec = software["input_files"]
        formatting_kwargs = {
            key: (input_files[key].name if key in input_files else "")
            for key in chain(files_spec["required"], files_spec["optional"])
        }
        commands = software["commands"].format(**formatting_kwargs)

        config_lines = (
            custom_config.script_lines.strip() + "\n" if custom_config else ""
        )
        with script_path.open("w") as f:
            f.write(
                settings.PORTAL_CONFIG["script_template"].format(
                    commands=commands,
                    resources=resources["script_lines"],
                    custom_config=config_lines,
                    job_name=f"portal_job_{job.job_number}",
                )
            )

        try:
            job_id = scheduler.submit(script_path, job.work_dir)
            job.job_id = job_id
            job.save()
            return job
        except scheduler.SchedulerError:
            job.delete()
            raise


class Job(models.Model):
    """A representation of a job run on a computing cluster."""

    STATUS_CHOICES = [("C", "Completed"), ("Q", "Queueing"), ("R", "Running")]

    status = models.CharField(max_length=1, choices=STATUS_CHOICES)
    job_id = models.CharField(max_length=20, blank=True)
    submission_time = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=200, blank=True)
    project = models.ForeignKey(
        "Project", on_delete=models.SET_NULL, null=True, blank=True
    )
    resources = models.CharField(max_length=100)
    software = models.CharField(max_length=50)
    _walltime = models.DurationField(blank=True, null=True)
    objects = JobManager()

    @property
    def work_dir(self):
        """The working directory for the job"""
        return settings.JOBS_DIR / self.job_number

    def delete(self):
        """Delete job instance, if not yet completed delete from scheduler and remove
        working directory from disk.
        """
        if self.status != "Completed" and self.job_id:
            scheduler.delete(self.job_id)
            # small wait to let the scheduler delete the job to try and
            # minimise issues with deleting the working directory
            time.sleep(2)
        shutil.rmtree(self.work_dir)
        super().delete()

    def get_absolute_url(self):
        """Return the absolute url for a Job instance"""
        return reverse("main:job", kwargs={"job_pk": self.pk})

    @property
    def walltime(self):
        """The elapsed execution time of the job as a string or timedelat. If the job is
        running this is looked up from using the WALLTIME file in the job working
        directory.
        """
        if self.status == "Completed":
            return "Unknown" if self._walltime is None else self._walltime
        elif self.status == "Queueing":
            return "N/A"
        else:
            # if job is not complete get the most up-to-date walltime from disk
            try:
                with (self.work_dir / "WALLTIME").open() as f:
                    return timedelta(seconds=int(f.read()))
            except (IOError, ValueError):
                return "Unknown"

    @property
    def published(self):
        """Whether this job has associated Publication records"""
        return bool(Publication.objects.filter(job=self).count())

    @walltime.setter
    def walltime(self, value):
        """Set the `_walltime` attribute of a job, rounded to nearest increment of
        ROUNDING_INTERVAL.

        Args:
          value (timedelta): the elapsed walltime

        Returns:
          None
        """
        # rounding is used to ensure that jobs which hit their full walltime
        # should have the correct value
        self._walltime = round(value / ROUNDING_INTERVAL) * ROUNDING_INTERVAL

    @property
    def job_number(self):
        """The full string representation of this job number with leading zeros"""
        return f"{self.pk:08d}"


class Publication(models.Model):
    """A representation of depositions in data repository service"""

    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    repo_label = models.CharField(max_length=20)
    repo_name = models.CharField(max_length=50)
    doi = models.CharField(max_length=30, unique=True)

    @property
    def link(self):
        """The URL associated with the DOI"""
        return "https://doi.org/" + self.doi


class Profile(models.Model):
    """Used to store profile data for the user. Intended that their should only ever be
    one instance though this is not enforced.
    """

    orcid_id = models.CharField(
        max_length=19, validators=[validate_orcid_id], verbose_name="ORCID iD"
    )
    given_names = models.CharField(max_length=100)
    family_name = models.CharField(max_length=40)
    affiliation = models.CharField(max_length=50)


class Project(models.Model):
    """A project grouping together multiple jobs."""

    name = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.name}"

    @property
    def number_of_jobs(self):
        """The number of jobs that are in this project"""
        return len(Job.objects.filter(project=self))


class Token(models.Model):
    """Used to store authentication tokens suitable for use with OAuth2 resources"""

    value = models.CharField(max_length=120)
    label = models.CharField(max_length=20, unique=True)
    refresh_token = models.CharField(max_length=120, blank=True)
    expires = models.DateTimeField(blank=True, null=True)
