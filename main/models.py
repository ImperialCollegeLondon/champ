import shutil
from itertools import chain

from django.conf import settings
from django.db import models

from . import scheduler

SCRIPT_CONTENTS = """#!/bin/bash
#PBS -l select=1:ncpus=1:mem=4gb
#PBS -l walltime=00:30:00

cd $PBS_O_WORKDIR

module load gaussian/g16-a03
[[ \"{fchk}\" != "" ]] && unfchk {fchk}
g16 {com}
"""


class JobManager(models.Manager):
    def create_job(self, description, input_files):
        job = self.create(status="Queueing", description=description)
        software = settings.SOFTWARE["gaussian16"]

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
        with script_path.open("w") as f:
            f.write(SCRIPT_CONTENTS.format(**formatting_kwargs))

        job_id = scheduler.submit(script_path, job.work_dir)
        job.job_id = job_id
        job.save()
        return job


class Job(models.Model):
    STATUS_CHOICES = [("C", "Completed"), ("Q", "Queueing"), ("R", "Running")]

    status = models.CharField(max_length=1, choices=STATUS_CHOICES)
    job_id = models.CharField(max_length=20, blank=True)
    submission_time = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=200, blank=True)
    objects = JobManager()

    @property
    def work_dir(self):
        return settings.JOBS_DIR / f"{self.pk:08d}"

    def delete(self):
        shutil.rmtree(self.work_dir)
        super().delete()
