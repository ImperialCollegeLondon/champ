import shutil
from itertools import chain

from django.conf import settings
from django.db import models
from django.urls import reverse

from . import scheduler
from .resources import RESOURCES

SCRIPT_TEMPLATE = """#!/bin/bash
{resources}

cd $PBS_O_WORKDIR

{commands}
"""


class JobManager(models.Manager):
    def create_job(
        self, description, input_files, project, resource_index, software_index
    ):
        resources = RESOURCES[resource_index]
        software = settings.SOFTWARE[software_index]
        job = self.create(
            status="Queueing",
            description=description,
            project=project,
            resources=resources["description"],
            software=software["name"],
        )

        job.work_dir.mkdir(parents=True)
        for inp in input_files.values():
            with (job.work_dir / inp.name).open("wb") as f:
                f.write(inp.read())

        script_path = job.work_dir / "sub.pbs"

        files_spec = software["input_files"]
        formatting_kwargs = {
            key: (input_files[key].name if key in input_files else "")
            for key in chain(files_spec["required"], files_spec["optional"])
        }

        commands = software["commands"].format(**formatting_kwargs)
        with script_path.open("w") as f:
            f.write(
                SCRIPT_TEMPLATE.format(
                    commands=commands, resources=resources["script_lines"]
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
    objects = JobManager()

    @property
    def work_dir(self):
        return settings.JOBS_DIR / f"{self.pk:08d}"

    def delete(self):
        shutil.rmtree(self.work_dir)
        super().delete()

    def get_absolute_url(self):
        return reverse("main:job", kwargs={"job_pk": self.pk})


class Project(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.name}"

    @property
    def number_of_jobs(self):
        return len(Job.objects.filter(project=self))
