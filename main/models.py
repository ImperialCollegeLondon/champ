import shutil

from django.conf import settings
from django.db import models

from . import scheduler

SCRIPT_CONTENTS = """#!/bin/bash
#PBS -l select=1:ncpus=1:mem=4gb
#PBS -l walltime=00:30:00

cd $PBS_O_WORKDIR

echo $(hostname)
sleep 1m
"""


class JobManager(models.Manager):
    def create_job(self):
        job = self.create(status="Queueing")
        job.work_dir.mkdir(parents=True)
        script_path = job.work_dir / "sub.pbs"
        with script_path.open("w") as f:
            f.write(SCRIPT_CONTENTS)
        job_id = scheduler.submit(script_path, job.work_dir)
        job.job_id = job_id
        job.save()
        return job


class Job(models.Model):
    STATUS_CHOICES = [("C", "Completed"), ("Q", "Queueing"), ("R", "Running")]

    status = models.CharField(max_length=1, choices=STATUS_CHOICES)
    job_id = models.CharField(max_length=20, blank=True)
    objects = JobManager()

    @property
    def work_dir(self):
        return settings.JOBS_DIR / f"{self.pk:08d}"

    def delete(self):
        super().delete()
        shutil.rmtree(self.work_dir)
