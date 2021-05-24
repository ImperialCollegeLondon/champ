import os
from itertools import chain
from urllib.parse import urlunparse

from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render

from . import scheduler
from .forms import JobForm, JobTypeForm, ProjectForm, SubmissionForm
from .models import Job, Project


def index(request):
    return render(request, "main/index.html")


def create_job(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk)
    if request.method == "POST":
        software = settings.SOFTWARE["gaussian16"]
        form = SubmissionForm(request.POST, request.FILES)
        files_spec = software["input_files"]
        if form.is_valid():
            input_files = {
                key: request.FILES[key]
                for key in chain(files_spec["required"], files_spec["optional"])
                if key in request.FILES
            }

            job = Job.objects.create_job(
                form.cleaned_data["description"], input_files, project
            )
            return redirect("main:success", job.pk)
    else:
        form = SubmissionForm()
    return render(request, "main/create_job.html", {"form": form})


def success(request, job_pk):
    job = Job.objects.get(pk=job_pk)
    return render(request, "main/success.html", {"job_id": job.job_id})


def list_jobs(request):
    jobs = Job.objects.all()[::-1]
    for job in jobs:
        if job.status != "Completed":
            job.status = scheduler.status(job.job_id).capitalize()
            job.save()

    scheme = "https" if request.is_secure() else "http"
    files_url = urlunparse(
        [scheme, request.get_host(), os.getenv("OOD_FILES_URL", ""), "", "", ""]
    )
    return render(
        request, "main/list_jobs.html", {"jobs": jobs, "files_url": files_url}
    )


def delete(request, job_pk):
    job = Job.objects.get(pk=job_pk)
    job.delete()
    return redirect(request.META.get("HTTP_REFERER", "main:index"))


def job_type(request):
    if request.method == "POST":
        form = JobTypeForm(request.POST)
        if form.is_valid():
            project = form.cleaned_data["project"]
            return redirect("main:create_job", project.pk)
    else:
        form = JobTypeForm()
    return render(request, "main/job_type.html", {"form": form})


def projects(request):
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(request.META.get("HTTP_REFERER", "main:index"))
    else:
        form = ProjectForm()
    projects = Project.objects.all()
    return render(request, "main/projects.html", {"projects": projects, "form": form})


def delete_project(request, project_pk):
    Project.objects.get(pk=project_pk).delete()
    return redirect(request.META.get("HTTP_REFERER", "main:index"))


def job(request, job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    form = JobForm(request.POST or None, instance=job)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            return redirect(request.META.get("HTTP_REFERER", "main:index"))
    return render(request, "main/job.html", {"form": form})
